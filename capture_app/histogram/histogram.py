from quart_trio import QuartTrio
from quart import request, send_file
import subprocess
import os
import json
from PIL import Image
import requests
from capture_app._response import returnResponse
from quart import Blueprint
from ._blueprint import blueprint

#  TODO move this to a centralized place
base_image_directory = "/home/telescope/captures/"

@blueprint.route("/", methods=["POST"])
async def get_histogram():
    res = await request.json
    try:
        image_url = base_image_directory + res['image']
        image_path = os.path.dirname(image_url)
        image_name= os.path.splitext(os.path.basename(image_url))[0]
        image_ext= os.path.splitext(os.path.basename(image_url))[1]
        dest_file= image_path + '/hist-'+image_name+image_ext
        cmd = '/usr/bin/convert ' + image_url + ' histogram:- | convert - ' + dest_file
        subprocess.call(cmd, shell=True)
        return await send_file(dest_file, mimetype='image/jpeg')
    except Exception as e:
        return await returnResponse({ "error": e.args[0] }, 404)

@blueprint.route("/save", methods=["POST"])
async def create_histogram():
    res = await request.json
    try:
        image_url = res['image']
        image_path = os.path.dirname(image_url)
        image_name= os.path.splitext(os.path.basename(image_url))[0]
        image_ext= os.path.splitext(os.path.basename(image_url))[1]
        dest_file= image_path + '/hist-'+image_name+image_ext
        cmd = '/usr/bin/convert ' + image_url + ' histogram:- | convert - ' + dest_file
        subprocess.call(cmd, shell=True)
        return await returnResponse({ "success": True }, 200)
    except Exception as e:
        return await returnResponse({ "error": e.args[0] }, 400)
        