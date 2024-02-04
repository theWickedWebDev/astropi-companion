import trio
from quart import request, make_response, current_app
from ._blueprint import blueprint
from src.logger.logger import Logger
import os
from dotenv import load_dotenv
log = Logger(__name__)
intervalometer: trio.CancelScope | None = None

load_dotenv('/home/pi/astropi-companion/.env')
BASE_IMAGE_DIRECTORY = os.environ['QUART_BASE_IMAGE_DIRECTORY']
# async def create_interval(interval: float or int, func, *args, task_status=trio.TASK_STATUS_IGNORED):


async def create_interval(name: str, frames: int, interval: float or int, exposure, camera):
    global intervalometer
    intervalometer = trio.CancelScope()
    with intervalometer:
        i = 0
        while i < frames:
            if (type(exposure) is int and exposure > 5):
                filename = await camera.capture_bulb(name, exposure, i)
            else:
                filename = await camera.capture_shutter(name, i)
            log.info(f'CAPTURED: {filename}')
            await trio.sleep(interval)
            i = i + 1


@blueprint.route('/start/', methods=['POST'])
async def start_intervalometer():
    try:
        global intervalometer

        if intervalometer:
            intervalometer.cancel()
            intervalometer = None

        camera = current_app.config.get('camera')
        intervalometer = trio.CancelScope()
        name = request.args.get('name')
        interval = request.args.get('interval')
        frames = request.args.get('frames')
        exposure = request.args.get('exposure')
        log.json({"name": name, "interval": interval,
                 "frames": frames, "exposure": exposure})
        blueprint.nursery.start_soon(
            create_interval, name, int(frames), float(interval), exposure, camera)
        return await make_response({"intervalometer": "started"}, 200)

    except Exception as e:
        print(e)
        return await make_response({"intervalometer": "not started", "error": e.args[0]}, 404)


@blueprint.route('/stop', methods=['POST'])
async def stop_intervalometer():
    try:
        global intervalometer

        if intervalometer:
            intervalometer.cancel()
            intervalometer = None

            return await make_response({"intervalometer": "stopped"}, 200)
        else:
            return await make_response({"intervalometer": "already stopped"}, 200)

    except Exception as e:
        print(e)
        return await make_response({"capture_interval": False, "error": e.args[0]}, 404)
