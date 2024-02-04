from quart_trio import QuartTrio
from dotenv import load_dotenv
import trio
import json
import logging
import sys
import os
from .web import web
from lib.telescope_class import Telescope
from lib.camera_class import create_camera, CameraRole
from lib.gphoto2 import get_available_usb_devices

try:
    with open(os.path.join('..', os.path.dirname(__file__), "logging.json"), "r") as f:
        import logging
        import logging.config

        logging.config.dictConfig(json.load(f))

except FileNotFoundError:
    pass


async def create_app():
    load_dotenv('.env')
    _app = QuartTrio(__name__)
    _app.config["TEMPLATES_AUTO_RELOAD"] = True
    _app.config["FLASK_DEBUG"] = True
    _app.config.update(
        MOCK_CAMERA_ENABLED='mock-camera' in sys.argv
    )
    _app.config.from_prefixed_env("QUART")

    available_cameras = await get_available_usb_devices()
    # cameras = [{"model": c.model, "port": c.port} for c in available_cameras]
    # TODO: Create front end to allow them to choose a camera
    if (len(available_cameras) > 0):
        PrimaryCam = await create_camera(
            camera=available_cameras[0],
            role=CameraRole.PRIMARY
        )

        _app.config['camera'] = PrimaryCam
    _app.config['available_cameras'] = available_cameras

    _app.register_blueprint(web, url_prefix="/")

    telescope = Telescope(mock_camera=True, mock_mount=True)
    _app.config['telescope'] = telescope
    return _app

app = trio.run(create_app)

app.run(
    host=app.config['APP_HOST'],
    port=app.config['APP_PORT'],
)
# app.run()
