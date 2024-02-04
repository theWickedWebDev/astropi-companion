from datetime import datetime
import numpy as np
from enum import Enum, auto
from astropy.coordinates import SkyCoord
import requests
import logging
import os
import json
from dotenv import load_dotenv
from web.util.platesolve.solve import solveField

load_dotenv('/home/pi/astropi-companion/local.env')

TELESCOPE_API_URL = os.environ['QUART_TELESCOPE_API_URL']
MOCKED_CALIBRATION_FRAME = os.environ['QUART_MOCKED_LIGHT_FRAME_G1_01_JPG']
PLATE_DELTA_TOLERANCE = os.environ['QUART_PLATE_DELTA_TOLERANCE']

class TelescopeJSON(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return super().encode(bool(obj))
        elif isinstance(obj, SkyCoord):
            return obj.to_string('hmsdms').split(' ')
        elif isinstance(obj, datetime):
            return obj.strftime("%m-%d-%Y %H:%M:%S")
        elif isinstance(obj, Target):
            return {
                "type": obj.type.name,
                "coords": obj.coords.to_string('hmsdms').split(' ') if hasattr(obj, 'coords') else "",
                "name": obj.name if hasattr(obj, 'name') else ""
            }
        else:
            return super().default(obj)


class TelescopeStatus(Enum):
    IDLE = auto()
    TRACKING = auto()


class TelescopeAction(Enum):
    CALIBRATE = "calibrate"
    GOTO = "goto"
    BUMP = "calibrate"


class TelescopeControlMethods(Enum):
    GOTO = auto()
    CALIBRATE = auto()
    IDLE = auto()


class TelescopeTargetTypes(Enum):
    RA_DEC = auto()
    SOLAR_SYSTEM = auto()
    BY_NAME = auto()


class Target():
    type: TelescopeTargetTypes
    coords: SkyCoord
    name: str

    def __init__(self, type: TelescopeTargetTypes, val: SkyCoord | str):
        self.type = type
        self.coords = val if TelescopeTargetTypes.RA_DEC else SkyCoord.from_name(val)


class TelescopeDeviation():
    time: datetime
    frame: str
    within_tolerance: bool
    solved: SkyCoord
    hmsdms: SkyCoord
    arcseconds: float


class PlateSolved():
    image_height: int
    image_width: int
    solved_image: str
    plot_layer_image: str
    annotated_image: str
    center: SkyCoord
    orientation: dict = {
        "south": float,
        "north": float
    }
    files: [str]
    # objects: [any]
    arcseconds_per_pixel: int
    bounds: tuple[SkyCoord, SkyCoord, SkyCoord, SkyCoord]


class TelescopeApiError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


class Telescope():
    _log: logging.Logger
    _mock_camera: bool
    _mock_mount: bool
    status: TelescopeStatus 
    target: Target = None
    target_coords: SkyCoord = None
    deviation: [TelescopeDeviation] = []
    last_solve: PlateSolved
    solves: [PlateSolved] = []

    def __init__(self, mock_camera: bool = False, mock_mount: bool = False):
        self._log = logging.getLogger(__name__)
        self.status = TelescopeStatus.IDLE
        self._mock_camera = mock_camera
        self._mock_mount = mock_mount
        self._log.info("TELESCOPE CREATED")

    async def platesolve(self):
        # TODO: Save the INDEX that was matched so it can solve
        # faster on subsequent solves
        self._log.info(f'Capturing Frame')
        # FIXME:
        capture_path = MOCKED_CALIBRATION_FRAME if self._mock_camera else MOCKED_CALIBRATION_FRAME

        self._log.info(f'Platesolving Astrometry.net')
        solved = await solveField(
            image_url=capture_path,
            returnWithPoints=False,
            noplots=True,
            skipsolved=False,
            ngc=True
        )

        self._save_solve(solved)

        if (hasattr(self, 'target')):
            new_target = Target(
                type=TelescopeTargetTypes.RA_DEC,
                val=self.last_solve.get('center')
            )
            self._set_target(new_target)

        within_tolerance = self._get_deviation()
        
        if (not within_tolerance):
            self._log.info(f'Calibrate Telescope')
            self.calibrate(self.target)
            self._log.info(f'GOTO Telescope')
            self.goto(self.target)

    def calibrate(self, target: Target):
        assert isinstance(target.type, TelescopeTargetTypes)
        self._set_target(target)
        self._control(target, TelescopeAction.CALIBRATE)
        self.status = TelescopeStatus.TRACKING
        self._log.info(f'Telescope Calibrated')

    def goto(self, target: Target):
        assert isinstance(target.type, TelescopeTargetTypes)
        self._set_target(target)
        self._control(target, TelescopeAction.GOTO)
        self.status = TelescopeStatus.TRACKING
        self._log.info(f'Telescope Slewed')

    def pause(self):
        self._api('/idle')
        self._log.info('Telescope Idling...')

    def bump(self, bearing: int = 0, dec: int = 0):
        """
        TODO: Calculate steps to pixels,
        or steps to degrees,
        or steps to arcseconds, etc.
        """
        self._log.info(f'Bumping telescope by bearing {
                       bearing}, dec {dec}, steps')
        url = '/calibrate/bump?sync=true'
        if (bearing > 0):
            url += f'&bearing={bearing}'
        if (dec > 0):
            url += f'&dec={dec}'

        self._api(url)

    def _api(self, uri: str):
        url = TELESCOPE_API_URL + uri

        try:
            res = requests.post(url)
            if not res.ok:
                raise Exception()

            self._log.info(f"{url} - {res.status_code}")
            return res
        except Exception as e:
            e.add_note('[Failed Telescope API]')
            e.add_note(url)
            raise

    def _control(self, target: Target, action: TelescopeAction):
        uri = action.value
        try:
            match target.type:
                case TelescopeTargetTypes.RA_DEC:
                    # There needs to be a better way to do this
                    [ra, dec] = str(target.coords.to_string(
                        'hmsdms')).replace('+', '').split(' ')
                    self._api(f"/{uri}?ra={ra}&dec={dec}")
                case TelescopeTargetTypes.BY_NAME:
                    self._api(f"/{uri}/by_name?name={target.name}")
                case TelescopeTargetTypes.SOLAR_SYSTEM:
                    self._api(
                        f"/{uri}/solar_system_object?name={target.name}")
        except Exception as e:
            self._log.error(e)
            raise

    def _set_target(self, target: Target):
        assert isinstance(target.type, TelescopeTargetTypes)
        self.target = target
        if (target.type == TelescopeTargetTypes.RA_DEC):
            self.target_coords = target.coords
        else:
            self.target_coords = SkyCoord.from_name(target.name)

    def _save_solve(self, solved):
        self._log.info(f'Saving Solve')
        self.last_solve = {
            "image_height": solved.get('data', {}).get('image_height'),
            "image_width": solved.get('data', {}).get('image_width'),
            "solved_image": solved.get('solved_image'),
            "plot_layer_image": solved.get('plot_layer_image'),
            "annotated_image": solved.get("annotated_image"),
            "center": solved.get('data', {}).get('center'),
            "orientation": solved.get('data', {}).get('orientation'),
            "arcseconds_per_pixel": solved.get('data', {}).get('arcseconds_per_pixel'),
            "files": solved.get('generated_files'),
            "points": solved.get('points'),
            "objects": solved.get('objects'),
            "bounds": solved.get('bounds'),
        }
        self.solves.append(self.last_solve)

    def _get_deviation(self):
        self._log.info(f'Calculate Deviation')
        solved_center_coords = self.last_solve.get('center')
        target_coords = self.target_coords

        ra_offset = (solved_center_coords.ra - target_coords.ra) * \
            np.cos(target_coords.dec.radian)
        dec_offset = (solved_center_coords.dec - target_coords.dec)
        
        tol = int(PLATE_DELTA_TOLERANCE)
        within_tolerance = bool(abs(dec_offset.to('arcsec').value) < tol and abs(ra_offset.to('arcsec').value) < tol)

        self.deviation.append({
            "time": datetime.now(),
            "frame": self.last_solve.get('solved_image'),
            "within_tolerance": within_tolerance,
            "solved": solved_center_coords,
            "arcseconds": self.last_solve.get('arcseconds_per_pixel'),
        })
        
        return within_tolerance
    
    def json(self):
        final_json = {}
        final_json.update({ "deviation": self.deviation})
        # final_json.update({ "solves": self.solves })
        final_json.update({ "data": self.last_solve })
        final_json.update({ "target": self.target })
        final_json.update({ "target_coords": self.target_coords })
        
        return json.dumps(final_json, cls=TelescopeJSON)
