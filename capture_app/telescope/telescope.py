from capture_app.util import returnResponse

from ._blueprint import blueprint

@blueprint.route('/start/', methods=['POST'])
async def start_telescope():
    try:
        return await returnResponse({"started": True}, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "started": False, "error": e.args[0] }, 404)

@blueprint.route('/stop/', methods=['POST'])
async def stop_telescope():
    try:
        return await returnResponse({"poweroff": True}, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "poweroff": False, "error": e.args[0] }, 404)

@blueprint.route('/restart/', methods=['POST'])
async def restart_telescope():
    try:
        return await returnResponse({"restarted": True}, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "restarted": False, "error": e.args[0] }, 404)


@blueprint.route('/calibrate/', methods=['POST'])
async def post_calibrate():
    try:
        return await returnResponse({"calibrate": True}, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "calibrate": False, "error": e.args[0] }, 404)

