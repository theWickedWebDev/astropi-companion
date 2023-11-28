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