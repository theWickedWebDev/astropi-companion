from quart import request, current_app
import trio
from ._blueprint import blueprint
from .config import config

scope: trio.CancelScope | None = None

from .config import config
from .control import control

blueprint.register_blueprint(control, url_prefix="/control")
blueprint.register_blueprint(config, url_prefix="/config")