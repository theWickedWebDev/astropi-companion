from .wifi import wifi
from .dashboard import dashboard
from ._blueprint import blueprint

blueprint.register_blueprint(dashboard, url_prefix="/")
blueprint.register_blueprint(wifi, url_prefix="/wifi")
