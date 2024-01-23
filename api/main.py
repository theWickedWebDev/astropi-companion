from quart_trio import QuartTrio
from dotenv import load_dotenv
from quart import session
from quart_session import Session
import sys
from .camera import camera
from .files import files
from .telescope import telescope
from .sessions import sessions

def create_app(mode='Development'):
    load_dotenv()
    _app = QuartTrio(__name__)
    _app.config['SESSION_TYPE'] = 'redis'
    _app.config.update(
        MOCK_CAMERA_ENABLED='mock-camera' in sys.argv
    )

    Session(_app)
    _app.config.from_prefixed_env("QUART")
    _app.register_blueprint(sessions, url_prefix="/sessions")
    _app.register_blueprint(camera, url_prefix="/camera")
    _app.register_blueprint(files, url_prefix="/files")
    _app.register_blueprint(telescope, url_prefix="/telescope")
    return _app

app = create_app()

app.run()