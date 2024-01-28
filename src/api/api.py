from .camera import camera
from .files import files
from .telescope import telescope
from .sessions import sessions
from ._blueprint import blueprint

blueprint.register_blueprint(sessions, url_prefix="/sessions")
blueprint.register_blueprint(camera, url_prefix="/camera")
blueprint.register_blueprint(files, url_prefix="/files")
blueprint.register_blueprint(telescope, url_prefix="/telescope")
