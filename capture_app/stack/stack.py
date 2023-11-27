from quart_trio import QuartTrio
from quart import request, current_app
import subprocess
import os
import json
from PIL import Image
from datetime import datetime
import requests
from capture_app._response import returnResponse
from quart import Blueprint
from ._blueprint import blueprint
from capture_app.util.get_lum_value import getLuminanceFromUrl
from capture_app.util.get_weather import getWeather

@blueprint.route("/new/", methods=["POST"])
async def create_new_stack():
    res = await request.json
    src_dir = current_app.config['BASE_IMAGE_DIRECTORY']
    try:
        stack_dir= src_dir + res['name']
        date_dir=datetime.now().strftime("/%m-%d-%Y")
        subprocess.run(['mkdir', '-p', stack_dir])

        for d in ["lights", "darks", "biases", "flats", "process", "masters", "samples"]:
            subprocess.run(['mkdir', '-p', stack_dir + date_dir + '/' + d])

        subprocess.run(['touch', stack_dir + date_dir + '/' + res['name'] + '.log'])
        return await returnResponse({ "name": res['name'] }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)


@blueprint.route("/status/<capture_name>/<capture_date>/", methods=["GET"])
async def get_stack_counts(capture_name, capture_date):
    try:
        base_path=current_app.config['BASE_IMAGE_DIRECTORY'] + capture_name + '/' + capture_date + '/'
        counts = {}

        for d in ["lights", "darks", "biases", "flats", "process", "masters", "samples"]:
            count = 0
            if os.path.exists(base_path + d):
                for path in os.listdir(base_path + d):
                    if os.path.isfile(os.path.join(base_path + d, path)):
                        count += 1
                counts[d] = count
        return await returnResponse({ "data": {
            "counts": counts
        } }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

