import trio
from quart import request
import subprocess
from capture_app._response import returnResponse
from capture_app.stack._blueprint import blueprint

scope: trio.CancelScope | None = None

BASE_IMAGE_DIRECTORY="/home/telescope/captures/"
CONFIG_FILE_NAME='config.ini'
CONFIG_KEYS=(
    "DATE",
    "TARGET_NAME",
    "TARGET_RA",
    "TARGET_DEC",
    "FRAMES",
    "ISO",
    "APERTURE",
    "EXPOSURE_SECONDS",
    "FOCAL",
    "IMAGEFORMAT",
    "AUTOEXPOSUREMODE",
    "PICTURESTYLE",
    "HISTOGRAM",
    "START_TIME",
    "END_TIME"
)

def getStackConfig(name):
    res = {}
    with open(BASE_IMAGE_DIRECTORY + name + '/' + CONFIG_FILE_NAME, 'r') as file:
        for line in file:
            line = line.strip()
            key, val = line.split('=')
            res.update({ key: val})
    
    vals = {}
    for key in res.keys():
        if key in CONFIG_KEYS:
            vals[key] = res[key]

    return vals

def setStackConfig(name, raw_vals):
    vals = {}
    error_keys = []
    for key in raw_vals.keys():
        if key in CONFIG_KEYS:
            vals[key] = raw_vals[key]
        else:
            error_keys.append("'" + key + "' is not a valid configuration property")
    res = getStackConfig(name)
    for key in vals.keys():
        res[key] = vals[key]
    subprocess.run(['rm', BASE_IMAGE_DIRECTORY + name + '/' + CONFIG_FILE_NAME])
    with open(BASE_IMAGE_DIRECTORY + name + '/' + CONFIG_FILE_NAME, 'w') as file:
        for key in res.keys():
            item=str(key) + '=' + str(res[key])
            file.write("%s\n" % item)
    return res, error_keys

@blueprint.route('/<stack_name>/', methods=['POST'])
async def set_stack_config(stack_name):
    res = await request.json
    try:
        config, error_keys = setStackConfig(stack_name, res)
        return await returnResponse({ "config": config, "errors": error_keys }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

@blueprint.route('/<stack_name>/', methods=['GET'])
async def get_stack_config(stack_name):
    try:
        config = getStackConfig(stack_name)
        return await returnResponse({ "config": config }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)
