from quart import current_app, make_response
import json
from src.logger.logger import Logger

from ._blueprint import blueprint
from . import telescope_class as t

log = Logger(__name__)


@blueprint.route('/calibrate/', methods=['POST'])
async def calibrate_telescope():

    # id: str
    # label: str
    # readonly: bool
    # type: Gphoto2DeviceConfigType
    # current: str
    # options

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
