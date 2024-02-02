import trio
from quart import make_response, jsonify, current_app
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


@blueprint.route('/settings/<setting>/<value>', methods=['POST'])
async def change_camera_setting(setting, value):
    try:
        cmd = f'gphoto2 --set-config-index {setting}="{value}"'
        await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
        return await make_response(jsonify({"success": True}), 200)
    except Exception as e:
        return await make_response(jsonify({"success": False}), 400)
