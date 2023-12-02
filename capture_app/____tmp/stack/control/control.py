import trio
from quart import request, current_app
import os
import subprocess
from capture_app._response import returnResponse
from ._blueprint import blueprint
from datetime import datetime
import glob
from ..config import config
from ..capture import capture

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
            for line in config.CONFIG_KEYS:
                log.write("%s\n" % str(line + '='))
        return await returnResponse({ "name": res['name'] }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)


@blueprint.route("/status/<capture_name>/", methods=["GET"])
async def get_stack_counts(capture_name):
    try:
        base_path=current_app.config['BASE_IMAGE_DIRECTORY'] + capture_name + '/'
        print('getStackConfig', config.getStackConfig(capture_name))
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
    global scope

    try:
        if scope:
            print('Stopping capture already in progress....')
            scope.cancel()
            scope = None
        scope = trio.CancelScope()

        blueprint.nursery.start_soon(capture, scope, capture_name)
        settings = config.getStackConfig(capture_name)
        return await returnResponse({ "started": capture_name, "config": settings }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

@blueprint.route('/stop/<capture_name>/', methods=['POST'])
async def stop_stack(capture_name):
    global scope

    try:
        scope.cancel()
        scope = None
        return await returnResponse({ "stopped": capture_name }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

@blueprint.route('/pause/<capture_name>/', methods=['POST'])
async def pause_stack(capture_name):
    global scope

    try:
        scope.cancel()
        scope = None
        return await returnResponse({ "paused": capture_name }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)