from datetime import datetime
from enum import Enum, auto
from astropy.coordinates import SkyCoord
import requests
import logging
import os

try:
    with open(os.path.join(os.path.dirname(__file__), "logging.json"), "r") as f:
        import json
        import logging.config

        logging.config.dictConfig(json.load(f))
except FileNotFoundError:
    pass

# mock
current_app = {
    "config": {
        "TELESCOPE_API_URL": "http://telescope.local:8765/api"
    }
}


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
        match self.type:
            case TelescopeTargetTypes.RA_DEC:
                self.coords = SkyCoord(val)
            case _:
                self.name = str(val)


class TelescopeDeviation():
    time: datetime
    frame: str
    within_tolerance: bool
    solved: SkyCoord
    hmsdms: SkyCoord
    arcseconds: SkyCoord


class PlateSolved():
    image_height: int
    image_width: int
    center: SkyCoord
    orientation: dict = {
        "south": float,
        "north": float
    }
    files: list[str]
    arcseconds_per_pixel: int
    # TopLeft, TopRight, BottomRight, BottomLeft
    bounds: tuple[SkyCoord, SkyCoord, SkyCoord, SkyCoord]


class TelescopeApiError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


class Telescope():
    _log: logging.Logger
    status: TelescopeStatus
    target: Target
    deviation: list[TelescopeDeviation]
    last_solve: PlateSolved

    def __init__(self):
        self._log = logging.getLogger(__name__)
        self.status = TelescopeStatus.IDLE

    def platesolve(self):
        self._log.info(f'Capturing Frame')
        self._log.info(f'Astrometry.net')
        # If target exists:
        self._log.info(f'Compare solved coords to target')
        self._log.info(f'Calculate Deviation')
        # else:
        self._log.info(f'Calibrate Telescope')
        # endif
        self._log.info(f'Store last_solve')

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
        url = str(current_app.get('config', {}).get(
            'TELESCOPE_API_URL')) + uri
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

#
#


targetRaDec = Target(type=TelescopeTargetTypes.RA_DEC,
                     val=SkyCoord(ra="10h3m22.33s", dec="68d43m51.4s"))

targetName = Target(type=TelescopeTargetTypes.BY_NAME, val="Andromeda")

targetSolar = Target(type=TelescopeTargetTypes.SOLAR_SYSTEM, val="Jupiter")

# t = Telescope()
# targ = targetRaDec
# t.calibrate(targ)
# t.goto(targ)
# print(t.target.coords)
# t.platesolve()
# t.bump(bearing=20)
