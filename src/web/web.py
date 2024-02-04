from .wifi import wifi
from .dashboard import dashboard
from .img import img
from .sequence import sequence
from ._blueprint import blueprint

blueprint.register_blueprint(dashboard, url_prefix="/")

blueprint.register_blueprint(wifi, url_prefix="/wifi/")
blueprint.register_blueprint(img, url_prefix="/img")
blueprint.register_blueprint(sequence, url_prefix="/sequence")
