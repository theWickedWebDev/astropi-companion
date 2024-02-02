from quart import current_app, make_response
import json
from src.logger.logger import Logger

from ._blueprint import blueprint
from . import telescope_class as t
from ..camera.camera import Camera, CameraType, ConfigName, SetConfig

log = Logger(__name__)

CALIBRATION_CAMERA_SETTINGS = {
    "iso": "3200",
    "aeb": "Off",
    "autoexposuremode": "MANUAL",
    "imageformat": "LG_FINE_JPG",
    "picturestyle": "STANDARD",
    "drivemode": "0",
    "shutterspeed": "4",
    "aperture": "5.6"
}


@blueprint.route('/calibrate/', methods=['POST'])
async def calibrate_telescope():

    PrimaryCamera = Camera(type=CameraType.PRIMARY, mocked=True)
    GuideCamera = Camera(type=CameraType.GUIDE, mocked=True)

    await PrimaryCamera.init()
    await PrimaryCamera.set_device(PrimaryCamera.available_devices[1])
    PrimaryCamera.capture()
    PrimaryCamera.preview()
    PrimaryCamera.record()

    a = SetConfig(name=ConfigName.APERTURE, value="5")
    b = SetConfig(name=ConfigName.SHUTTERSPEED, value="1/10")
    c = SetConfig(name=ConfigName.ISO, value="400")

    PrimaryCamera.set_config([a, b, c])

    return await make_response({}, 200)
    try:
        telescope: t.Telescope = current_app.config.get('telescope')

        #  FIXME: Dont need target, if no target, then capture first
        #  and use solve results as target (skip deviations)
        # target = t.Target(type=t.TelescopeTargetTypes.RA_DEC,
        #                   val=SkyCoord(ra="10h3m22.33s", dec="68d43m51.4s"))

        # telescope.calibrate(target)
        await telescope.platesolve()
        return await make_response(json.loads(telescope.json()), 200)

    except Exception as e:
        print(e)
        print(e.args)
        return await make_response({"message": "There was an error calibrating the telescope", "error": e.args}, 400)
