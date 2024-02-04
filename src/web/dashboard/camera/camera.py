import trio
from quart import make_response, jsonify, current_app, request
from ._blueprint import blueprint

@blueprint.route('/capture', methods=['POST'])
async def capture():
    try:
        TMP_CALIBRATION_FRAME_LOCATION = f"{
            current_app.config['TMP_CALIBRATION_FRAME_LOCATION']}"
        # capture_res = await capturePhoto({}, TMP_CALIBRATION_FRAME_LOCATION)
        return await make_response({}, 200)

    except Exception as e:
        return await make_response(jsonify({"failed": True}), 400)

@blueprint.route('/preview', methods=['POST'])
async def preview():
    try:
        camera = current_app.config.get('camera')
        filename = await camera.capture_preview()
        return await make_response(jsonify({"success": True, "file": filename }), 200)
    except Exception as e:
        return await make_response(jsonify({"success": False}), 400)


@blueprint.route('/settings', methods=['POST'])
async def change_camera_setting():
    try:
        setting = request.args.get('setting')
        index = request.args.get('index')
        by_value = request.args.get('by_value') == 'true'
        custom = request.args.get('custom') == 'true'
        camera = current_app.config.get('camera')
        await camera.set_config(setting, index, by_value, custom)
        return await make_response(jsonify({"success": True}), 200)
    except Exception as e:
        return await make_response(jsonify({"success": False}), 400)


@blueprint.route('/settings/save', methods=['POST'])
async def save_camera_setting():
    try:
        name = request.args.get('name')
        camera = current_app.config.get('camera')
        await camera.save_config(name)
        return await make_response(jsonify({"success": True}), 200)
    except Exception as e:
        return await make_response(jsonify({"success": False}), 400)
