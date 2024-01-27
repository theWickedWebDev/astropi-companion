from ._blueprint import blueprint
from .capture import capture
from .intervalometer import intervalometer

blueprint.register_blueprint(capture, url_prefix="/capture")
blueprint.register_blueprint(intervalometer, url_prefix="/interval")
