from quart_trio import QuartTrio
from dotenv import load_dotenv

from .camera import camera
from .files import files
from .telescope import telescope


def create_app(mode='Development'):
    load_dotenv()
    _app = QuartTrio(__name__)
    _app.config.from_prefixed_env("QUART")
    _app.register_blueprint(camera, url_prefix="/camera")
    _app.register_blueprint(files, url_prefix="/files")
    _app.register_blueprint(telescope, url_prefix="/telescope")
    return _app

app = create_app()

app.run()