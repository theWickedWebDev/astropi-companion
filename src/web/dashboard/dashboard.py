import trio
from quart import render_template, current_app
import requests
import re
import os
import json

from ._blueprint import blueprint
from ..sequence.sequence import get_sequences


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
    # config = await get_camera_config()
    tele = read_telescope_file()
    weather = fetchWeather()
    sequences = get_sequences()

    return await render_template(
        page,
        telescope=tele,
        sequences=sequences,
        camera_config={},  # config,
        weather=weather
    )


@blueprint.route('/', methods=['GET'])
async def index():
    return await render_dashboard('pages/dashboard/dashboard.html')


@blueprint.route('/camera', methods=['GET'])
async def camera():
    return await render_dashboard('pages/dashboard/camera.html')


@blueprint.route('/telescope', methods=['GET'])
async def telescope():
    return await render_dashboard('pages/dashboard/telescope.html')
