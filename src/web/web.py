from .wifi import wifi
from ._blueprint import blueprint

blueprint.register_blueprint(wifi, url_prefix="/wifi")
