from quart_trio import QuartTrio
from dotenv import load_dotenv
import trio
# from quart_session import Session
import json
import logging
import sys
import os
from .web import web
from .web.telescope.telescope_class import Telescope
from web.camera.camera_class import get_available_usb_devices, create_gphoto2device, Gphoto2DeviceRole

try:
    with open(os.path.join('..', os.path.dirname(__file__), "logging.json"), "r") as f:
        import logging
        import logging.config

        logging.config.dictConfig(json.load(f))

except FileNotFoundError:
    pass


def create_app(mode):

    if (mode == 'Development'):
        load_dotenv('./local.env')
    else:
        load_dotenv('./prod.env')

    _app = QuartTrio(__name__)
    _app.config["TEMPLATES_AUTO_RELOAD"] = True
    _app.config["FLASK_DEBUG"] = True
    _app.config.update(
        MOCK_CAMERA_ENABLED='mock-camera' in sys.argv
    )
    _app.config.from_prefixed_env("QUART")
    _app.register_blueprint(web, url_prefix="/")

    telescope = Telescope(mock_camera=True, mock_mount=True)
    _app.config['telescope'] = telescope
    return _app


PrimaryCam = None
availableCameras = []


async def init():
    global PrimaryCam
    global availableCameras
    availableCameras = await get_available_usb_devices()
    cameras = [{"model": c.model, "port": c.port} for c in availableCameras]
    # print('Available Cameras')
    # for i, c in enumerate(cameras):
    #     print(f'{i+1}: {c.get("model")}')

    PrimaryCam = await create_gphoto2device(
        camera=availableCameras[0],
        role=Gphoto2DeviceRole.PRIMARY
    )

trio.run(init)

# if __name__ == '__main__':
if os.environ['ENV'] == 'prod':
    app = create_app(mode="PRODUCTION")
else:
    app = create_app(mode="DEVELOPMENT")

app.config['camera'] = PrimaryCam
app.config['availableCameras'] = availableCameras

app.run(
    host=app.config['APP_HOST'],
    port=app.config['APP_PORT'],
)
# app.run()
