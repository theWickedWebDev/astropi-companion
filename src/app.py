from quart_trio import QuartTrio
from dotenv import load_dotenv
from quart_session import Session
import sys
from .api import api
from .web import web


def create_app(mode='Development'):
    load_dotenv()
    _app = QuartTrio(__name__)
    _app.config['SESSION_TYPE'] = 'redis'
    _app.config["TEMPLATES_AUTO_RELOAD"] = True
    _app.config["FLASK_DEBUG"] = True
    _app.config.update(
        MOCK_CAMERA_ENABLED='mock-camera' in sys.argv
    )

    Session(_app)
    _app.config.from_prefixed_env("QUART")
    _app.register_blueprint(api, url_prefix="/api")
    _app.register_blueprint(web, url_prefix="/")
    return _app


# if __name__ == '__main__':
app = create_app()

app.run(host='0.0.0.0', port=5000, debug=True)
app.run()
