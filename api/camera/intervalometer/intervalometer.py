import trio
from quart import request
from api.util import returnResponse
from ._blueprint import blueprint

intervalometer: trio.CancelScope | None = None

# async def create_interval(interval: float or int, func, *args, task_status=trio.TASK_STATUS_IGNORED):
async def create_interval(frames: int, interval: float or int, task_status=trio.TASK_STATUS_IGNORED):
    global intervalometer
    with intervalometer:
        task_status.started(intervalometer)
        i = frames
        while i > 0:
            await trio.sleep(interval)
            # await capture_single_frame()
            i = i - 1

@blueprint.route('/start/', methods=['POST'])
async def start_intervalometer():
    try:        
        global intervalometer
        
        if intervalometer:
            return await returnResponse({ "intervalometer": "already started" }, 200)
        
        intervalometer = trio.CancelScope()

        request_json = await request.json
        config = request_json.get('config', {})
        interval = config.get('interval', 1)
        frames = config.get('frames', 1)
        
        blueprint.nursery.start_soon(create_interval, int(frames), float(interval))
        return await returnResponse({ "intervalometer": "started" }, 200)
            
    except Exception as e:
        print(e)
        return await returnResponse({ "intervalometer": "not started", "error": e.args[0] }, 404)

@blueprint.route('/stop', methods=['POST'])
async def stop_intervalometer():
    try:        
        global intervalometer

        if intervalometer:
            intervalometer.cancel()
            intervalometer = None

            return await returnResponse({ "intervalometer": "stopped" }, 200)
        else:
            return await returnResponse({ "intervalometer": "already stopped" }, 200)
            
    except Exception as e:
        print(e)
        return await returnResponse({ "capture_interval": False, "error": e.args[0] }, 404)
