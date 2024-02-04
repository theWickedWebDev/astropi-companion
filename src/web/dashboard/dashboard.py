from quart import render_template, current_app
import requests
import os
import json

from ._blueprint import blueprint
from ..sequence.sequence import get_sequences
from .camera.camera_class import get_available_usb_devices
from .camera import camera
from .telescope import telescope

blueprint.register_blueprint(camera, url_prefix="/camera")
blueprint.register_blueprint(telescope, url_prefix="/telescope")


def get_camera_config():
    return {}


def fetchWeather():
    WEATHER_API_URL = current_app.config['WEATHER_API_URL']

    try:
        weather = {}
        r = requests.get(WEATHER_API_URL)
        weather_data = r.json().split()

        for idx, k in enumerate(["temperature", "wind", "moonphase", "moonday", "precipitation", "zenith", "humidity", "condition"]):
            weather[k] = weather_data[idx]

        temp_f = weather["temperature"].replace('°F', '').replace('+', '')
        temp = (float(temp_f)-32)*(5/9)
        humidity_pc = weather["humidity"].replace('%', '')
        humidity = float(humidity_pc)/100

        return {
            **weather,
            "temp_val": temp,
            "humidity_val": humidity
        }
    except Exception as e:
        print(e)
        return {}


def read_telescope_file():
    telescope_file = current_app.config['BASE_TELESCOPE_JSON']
    data = {}
    if not os.path.isfile(telescope_file):
        with open(telescope_file, 'w') as f:
            f.write(json.dumps({}, indent=2))

    with open(telescope_file, 'r') as f:
        data = f.read()

    return json.loads(data)


async def render_dashboard(page):
    tele = read_telescope_file()
    weather = fetchWeather()
    sequences = get_sequences()
    _cameras = await get_available_usb_devices()
    cameras = [{"model": c.model, "port": c.port} for c in _cameras]

    camera = current_app.config.get('camera')
    primary, secondary, _ = camera.get_json_config()

    camera_details = {
        "name": camera.camera.model,
        "lensname": camera.lensname
    }

    return await render_template(
        page,
        telescope=tele,
        sequences=sequences,
        cameras=cameras,
        camera=camera_details,
        camera_config=primary,
        camera_config_secondary=sorted(secondary, key=lambda x: x['readonly']),
        weather=weather
    )


@blueprint.route('/', methods=['GET'])
async def index():
    return await render_dashboard('pages/dashboard/index.jinja')


@blueprint.route('/camera', methods=['GET'])
async def camera():
    return await render_dashboard('pages/dashboard/camera/index.jinja')


@blueprint.route('/telescope', methods=['GET'])
async def telescope():
    return await render_dashboard('pages/dashboard/telescope/index.jinja')
