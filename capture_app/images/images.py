from quart_trio import QuartTrio
from quart import request, send_file
import subprocess
import json
import os
import json
from PIL import Image
import requests
from capture_app._response import returnResponse
from quart import Blueprint
from ._blueprint import blueprint
import glob
import re


#  TODO move this to a centralized place
base_image_directory = "/home/telescope/captures/"

@blueprint.route('/list/', defaults={'path': ''})
@blueprint.route("/list/<path:path>", methods=["GET"])
async def list_images(path):
    print('bang')
    try:
        image_directory = base_image_directory

        if path:
            image_directory = image_directory + path

        if image_directory[-1] != '/':
            image_directory = image_directory + '/'
            
        print(image_directory)
        
        _list = glob.glob(image_directory + '*', recursive=True)
        print(_list)
        _filtered_files = [x.replace(base_image_directory, '') for x in _list]
        filtered_files = [x for x in _filtered_files if '.' in x and ('.jpg' in x or '.cr2' in x or '.png' in x)]
        _filtered_stacks = [x.replace(image_directory, '') for x in _list]
        filtered_stacks = [x for x in _filtered_stacks if '.' not in x]

        return await returnResponse({ "files": filtered_files, "stacks": filtered_stacks }, 200)
    except Exception as e:
        return await returnResponse({ "error": e.args[0] }, 404)


@blueprint.route('/', defaults={'path': ''})
@blueprint.route('/<path:path>')
async def get_img(path):
    try:
        size = int(request.args.get('size', default=0))
        img_path = base_image_directory + path

        if (size != 0):
            tmp_img = '/tmp/' + img_path[1:].replace("/", ".")

            image = Image.open(img_path)
            image.thumbnail((size,size), Image.Resampling.LANCZOS)
            image.save(tmp_img)

            return await send_file(tmp_img)
        else:
            return await send_file(img_path)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)