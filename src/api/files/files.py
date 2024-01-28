from ._blueprint import blueprint
from .annotate import annotate
from .exif import exif
from .manager import manager
from .plate import platesolve
from .histogram import histogram

blueprint.register_blueprint(manager, url_prefix="/")
blueprint.register_blueprint(annotate, url_prefix="/annotate")
blueprint.register_blueprint(exif, url_prefix="/exif")
blueprint.register_blueprint(platesolve, url_prefix="/plate")
blueprint.register_blueprint(histogram, url_prefix="/histogram")
