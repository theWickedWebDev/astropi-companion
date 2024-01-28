from quart import render_template, session, current_app

from ._blueprint import blueprint
from ...api import util as u
from ...api.sessions.sessions import getSessions


@blueprint.route('/', methods=['GET'])
async def index():
    response = getSessions()
    session_id = session.get("active_capture_session")
    activeSession = dict

    BASE_SESSIONS_DIRECTORY = f"{
        current_app.config['BASE_SESSIONS_DIRECTORY']}"
    session_file = f"{BASE_SESSIONS_DIRECTORY}{session_id}.json"

    if (session_id and u.session_exists(session_id)):
        activeSession = await u.get_session_data(session_file)

    print('\n')
    print('sessions')
    print(response)
    return await render_template(
        'pages/dashboard.html',
        sessions=response,
        activeSession=activeSession
    )
