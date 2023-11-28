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
from .util.config import getStackConfig, setStackConfig, CONFIG_KEYS
import glob

@blueprint.route('/list/', defaults={'path': ''})
@blueprint.route("/list/<path:path>", methods=["GET"])
async def list_images(path):
    print('bang')
    try:
        image_directory = current_app.config['BASE_IMAGE_DIRECTORY']

        if path:
            image_directory = image_directory + path

        if image_directory[-1] != '/':
            image_directory = image_directory + '/'
            
        print(image_directory)
        
        _list = glob.glob(image_directory + '*', recursive=True)
        print(_list)
        _filtered_files = [x.replace(current_app.config['BASE_IMAGE_DIRECTORY'], '') for x in _list]
        # filtered_files = [x for x in _filtered_files if '.' in x and ('.jpg' in x or '.cr2' in x or '.png' in x)]
        filtered_files = [x for x in _filtered_files if '.' in x]
        _filtered_stacks = [x.replace(image_directory, '') for x in _list]
        filtered_stacks = [x for x in _filtered_stacks if '.' not in x]

        return await returnResponse({ "files": filtered_files, "stacks": filtered_stacks }, 200)
    except Exception as e:
        return await returnResponse({ "error": e.args[0] }, 404)

@blueprint.route("/new/", methods=["POST"])
async def create_new_stack():
    res = await request.json
    src_dir = current_app.config['BASE_IMAGE_DIRECTORY']
    try:
        stack_dir= src_dir + res['name']
        date_dir=datetime.now().strftime("/%m-%d-%Y %H:%M:%S")
        subprocess.run(['mkdir', '-p', stack_dir])

        for d in ["lights", "darks", "biases", "flats", "process", "masters", "samples"]:
            subprocess.run(['mkdir', '-p', stack_dir + '/' + d])

        subprocess.run(['touch', stack_dir + '/stack.log'])

        with open(stack_dir + '/stack.log', 'w') as log:
            log.write("%s\n" % "Created: " + date_dir)

        subprocess.run(['touch', stack_dir + '/config.ini'])

        with open(stack_dir + '/config.ini', 'w') as log:
            for line in CONFIG_KEYS:
                log.write("%s\n" % str(line + '='))
        return await returnResponse({ "name": res['name'] }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

@blueprint.route('/config/<capture_name>/', methods=['POST'])
async def set_stack_config(capture_name):
    res = await request.json
    try:
        config, error_keys = setStackConfig(capture_name, res)
        return await returnResponse({ "config": config, "errors": error_keys }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

@blueprint.route('/config/<capture_name>/', methods=['GET'])
async def get_stack_config(capture_name):
    try:
        config = getStackConfig(capture_name)
        return await returnResponse({ "config": config }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

@blueprint.route("/status/<capture_name>/", methods=["GET"])
async def get_stack_counts(capture_name):
    try:
        base_path=current_app.config['BASE_IMAGE_DIRECTORY'] + capture_name + '/'
        print('getStackConfig', getStackConfig(capture_name))
        # Get counts of all images
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

@blueprint.route('/start/<capture_name>/', methods=['POST'])
async def start_stack(capture_name):
    try:
        config = getStackConfig(capture_name)
        return await returnResponse({ "config": config }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)
