from quart import request, current_app, session
import uuid
import glob
import json
import os
from pydantic.v1.utils import deep_update
from astropy.coordinates import SkyCoord
import datetime
from dateutil import parser

from ._blueprint import blueprint
from .. import util as u


def validateCreateSessionBody(body):
    lens = body.get('camera', {}).get('lens', None)
    target = body.get('target', {})

    if (lens == None or len(lens.items()) == 0):
        return {"message": "Lens object is required"}
    if (lens.get('name') == None):
        return {"message": "Lens name is required"}
    if (lens.get('focal_length') == None):
        return {"message": "Lens focal_length is required"}
    if (lens.get('aperture') == None):
        return {"message": "Lens aperture is required"}

    types = [e.value for e in u.TelescopeTargetTypes]

    if (target == None or len(target.items()) == 0):
        return {"message": "Valid target object is required"}
    if (target.get('key') == None or target.get('key') not in types):
        return {"message": "Valid target key is required: " + ' | '.join(types)}
    if (target.get('value') == None):
        valuemsg = ''
        match target.get('key'):
            case u.TelescopeTargetTypes.RA_DEC.value:
                valuemsg = {
                    "value": {
                        "ra": "HMS",
                        "dec": "DMS",
                    }
                }
            case u.TelescopeTargetTypes.BY_NAME.value:
                valuemsg = {"value": "polaris"}
            case _:
                valuemsg = {"value": "jupiter"}
        return {"message": "Target Value is required:", "hint": valuemsg}

    match target.get('key'):
        case u.TelescopeTargetTypes.RA_DEC.value:
            if (type(target.get('value')) is not dict):
                valuemsg = {
                    "value": {
                        "ra": "hms",
                        "dec": "dms",
                    }
                }
                return {"message": "Target Value incorrect format: ", "hint": valuemsg}
            if (target.get('value').get('ra') == None):
                return {"message": "Target RA is required", "hint": {"ra": "hms"}}
            if (target.get('value').get('dec') == None):
                return {"message": "Target DEC is required", "hint": {"dec": "dms"}}

            try:
                SkyCoord(ra=target.get('value').get('ra'),
                         dec=target.get('value').get('dec'))
            except Exception as e:
                return {"message": "Target coordinates are not valid", "hint": e.args}
        case u.TelescopeTargetTypes.BY_NAME.value:
            #  TODO: { "value": "polaris" }
            return True
        case _:
            #  TODO: { "value": "jupiter" }
            return True
    return True


def getSessions(showCompleted=True):
    BASE_SESSIONS_DIRECTORY = f"{
        current_app.config['BASE_SESSIONS_DIRECTORY']}"
    sessions = []
    _list = glob.glob(f"{BASE_SESSIONS_DIRECTORY}*", recursive=True)
    # TODO: Sort by date_range.starts instead?
    _list.sort(key=os.path.getmtime, reverse=True)

    for session_file in _list:
        session_data = u.get_session_data(session_file)
        details = session_data.get('details', {})
        iso_datetime = None
        if (session_data.get('details', {}).get("scheduled_start", None)):
            iso_datetime = parser.parse(session_data.get(
                'details', {}).get("scheduled_start", None)).strftime("%d/%m/%Y %H:%M:%S")

        data = {
            "id": session_data.get('id'),
            "name": details.get('name', None),
            "description": details.get('description', None),
            "status": session_data.get('status', None),
            "start": iso_datetime
        }

        if (
            (showCompleted and session_data.get(
                'status') == u.Statuses.COMPLETED.value)
            or (not session_data.get('status') == u.Statuses.COMPLETED.value)
        ):
            # sessions.append(appendGeneratedData(session_file, data))
            sessions.append(data)
    return sessions


@blueprint.route("/", methods=["GET"])
async def get_capture_sessions():

    showCompleted = bool(request.args.get('completed', default=False))

    try:
        sessions = getSessions(showCompleted=showCompleted)

        return await u.returnResponse(sessions, 200)

    except Exception as e:
        return await u.returnResponse({"message": "There was an error fetching session", "errors": e}, 400)


@blueprint.route('/active', methods=['GET'])
async def get_active_session_by_id():
    session_id = session.get("active_capture_session")
    print('\n')
    print('session_id')
    print(session_id)
    print('\n')
    if (session_id and u.session_exists(session_id)):
        return await get_session_by_id(session_id)
    else:
        return await u.returnResponse({}, 404)


@blueprint.route('/<id>', methods=['GET'])
async def get_session_by_id(id):
    BASE_SESSIONS_DIRECTORY = f"{
        current_app.config['BASE_SESSIONS_DIRECTORY']}"
    session_file = f"{BASE_SESSIONS_DIRECTORY}{id}.json"

    if (not u.session_exists(id)):
        return await u.returnResponse({}, 404)
    try:
        return await u.returnResponse(u.get_session_data(session_file), 200)

    except:
        return await u.returnResponse({"message": "There was an error fetching the session"}, 400)


# TODO: Move to /camera API
@blueprint.route('/options', methods=['GET'])
async def get_session_capture_options():
    return await u.returnResponse(u.CAMERA_SETTINGS_DICT_BY_NAME, 200)


@blueprint.route('/start/<session_id>', methods=['POST'])
async def start_session_by_id(session_id):
    BASE_SESSIONS_DIRECTORY = f"{
        current_app.config['BASE_SESSIONS_DIRECTORY']}"
    session_file = f"{BASE_SESSIONS_DIRECTORY}{session_id}.json"

    if (not u.session_exists(session_id)):
        return await u.returnResponse({}, 404)

    if (session.get('active_capture_session') == session_id):
        return await u.returnResponse({"error": 'This session is already started'}, 400)
    if (session.get('active_capture_session') and not session.get('active_capture_session') == session_id):
        return await u.returnResponse({
            "error": 'A different session is already started',
            'message': f'Stop {session.get("active_capture_session")} before starting another'
        }, 400)

    try:
        session_data = u.get_session_data(session_file)

        try:
            connected_lens_name = await u.getCurrentConfigValue('lensname')
            connected_lens_aperture = await u.getCurrentConfigValue('aperture')
        except Exception as e:
            print(e)
            return await u.returnResponse({'error': 'Camera Pi not responding'}, 400)

        camera = session_data.get('camera', {})
        lens = camera.get('lens', {})
        config_lens_name = lens.get('name')
        config_lens_aperture = lens.get('aperture')
        telescope_target = session_data.get('target')

        if (not current_app.config.get('MOCK_CAMERA_ENABLED')):
            try:
                # Asserts the correct lens has been attached
                if (connected_lens_name != config_lens_name):
                    raise Exception(f"{config_lens_name} is configured, however {
                                    connected_lens_name} is currently attached")

                # Set correct aperture value for lens
                if (str(connected_lens_aperture) != str(config_lens_aperture)):
                    await u.setCurrentConfigValue('aperture', config_lens_aperture)
                # Set other camera settings
                camera_config, _ = u.generateCameraConfigDict(
                    camera.get('config', {}))
                await u.setCameraSettings(camera_config)
            except Exception as e:
                print(e)
                return await u.returnResponse({'error': 'Camera Pi not responding'}, 400)
        # TELESCOPE API REQUEST TO GOTO TARGET COORDINATES
        try:
            u.controlTelescope(
                u.TelescopeControlMethods.CALIBRATE.value, telescope_target)
            try:
                u.controlTelescope(
                    u.TelescopeControlMethods.GOTO.value, telescope_target)
            except Exception as e:
                return await u.returnResponse({
                    "message": "Session not started. Unable to Slew Telescope",
                    "error": e.args
                }, 400)
        except Exception as e:
            return await u.returnResponse({
                "message": "Session not started. Unable to calibrate Telescope",
                "error": e.args
            }, 400)

        session['active_capture_session'] = session_id
        return await u.returnResponse(u.get_session_data(session_file), 200)
    except Exception as e:
        session['active_capture_session'] = None
        return await u.returnResponse({"message": "There was an error starting the session", "error": e}, 400)


@blueprint.route('/stop', methods=['POST'])
async def stop_session_by_id():
    id = session.get('active_capture_session')
    if (not id):
        return await u.returnResponse({"error": "No active session to stop"}, 404)
    else:
        session['active_capture_session'] = None
        return await u.returnResponse({"success": "stopped"}, 200)


@blueprint.route('/', methods=['POST'])
async def create_new_session():
    sessions_directory = f"{current_app.config['BASE_SESSIONS_DIRECTORY']}"

    try:
        body = await request.json

        valid = validateCreateSessionBody(body)
        if (valid is not True):
            return await u.returnResponse({"error": valid}, 400)

        details = body.get('details', {})
        frames = body.get('frames', None)
        camera_settings = body.get('camera', {}).get('config', None)
        lens = body.get('camera', {}).get('lens', None)
        target = body.get('target', {})

        sessionId = str(uuid.uuid4())
        new_session_file = f"{sessions_directory}/{sessionId}.json"

        if not os.path.isfile(new_session_file):
            new_session_data = {
                "id": sessionId,
                "details": details,
                "camera": {
                    "config": camera_settings,
                    "lens": lens
                },
                "target": target,
                "frames": {
                    "required": frames
                }
            }

            with open(new_session_file, 'w') as f:
                f.write(json.dumps(deep_update(
                    u.EMPTY_SESSION_DATA, new_session_data), indent=2))

            return await u.returnResponse(u.appendGeneratedData(new_session_file), 201)
        else:
            return await u.returnResponse({"message": "Session with ID already exists"}, 400)

    except Exception as e:
        print(e)
        return await u.returnResponse({"message": "There was an error generating a new session", "errors": e.args}, 400)


@blueprint.route('/<id>', methods=['DELETE'])
async def delete_session_by_id(id):
    BASE_SESSIONS_DIRECTORY = f"{
        current_app.config['BASE_SESSIONS_DIRECTORY']}"

    if (not u.session_exists(id)):
        return await u.returnResponse({}, 404)

    try:
        os.remove(f"{BASE_SESSIONS_DIRECTORY}{id}.json")
        return await u.returnResponse({'deleted': 'success', 'id': id}, 200)

    except:
        return await u.returnResponse({"message": "There was an error fetching the session"}, 400)


# TODO: Data needs to be validated
@blueprint.route('/<id>', methods=['PATCH'])
async def patch_session_by_id(id):
    BASE_SESSIONS_DIRECTORY = f"{
        current_app.config['BASE_SESSIONS_DIRECTORY']}"

    if (not u.session_exists(id)):
        return await u.returnResponse({}, 404)

    try:
        body = await request.json
        session_file = f"{BASE_SESSIONS_DIRECTORY}{id}.json"
        return await u.returnResponse(u.deep_update_session(session_file, body), 200)

    except Exception as e:
        return await u.returnResponse({"message": "There was an error patching the session", "error": e}, 400)
