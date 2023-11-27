from quart_trio import QuartTrio
from quart import request, current_app
import subprocess
import os
import json
from PIL import Image
import requests
from capture_app._response import returnResponse
from quart import Blueprint
from ._blueprint import blueprint
from capture_app.util.get_lum_value import getLuminanceFromUrl
from capture_app.util.get_weather import getWeather

@blueprint.route("/", methods=["POST"])
async def annotate_image():
    res = await request.json

    try:
        image_url = res['image']
        annotations = res['annotations']
        # 
        image_path = os.path.dirname(image_url)
        image_name= os.path.splitext(os.path.basename(image_url))[0]
        image_ext= os.path.splitext(os.path.basename(image_url))[1]
        dest_file= image_path + image_name + '-annotated' + image_ext
        
        if 'annotations' in res.keys():
            # Luminance Annotation
            cur_src=current_app.config['BASE_IMAGE_DIRECTORY'] + image_url
            cur_dest=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file

            if 'luminance' in annotations:                
                lum = getLuminanceFromUrl(cur_src)

                lum_val = "Lum: " + str(round(lum)) + "%"

                luminance_script = [
                    'convert',
                    cur_src,
                    '-gravity',
                    'SouthEast',
                    '-stroke',
                    '#000C',
                    '-pointsize',
                    "160",
                    '-strokewidth',
                    '2',
                    '-annotate',
                    '0',
                    lum_val,
                    '-stroke',
                    'none',
                    '-pointsize',
                    "160",
                    '-fill',
                    'white',
                    '-annotate',
                    '0',
                    lum_val,
                    cur_dest
                ]                

                subprocess.run(luminance_script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cur_src=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file
                cur_dest=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file

            # Exposure Annotation
            if 'exposure' in annotations:
                exposure_val="ISO1600\\ f\/5.6\\ 1\/100\""
                exposure_script = [
                    'convert',
                    cur_src,
                    '-gravity',
                    'SouthWest',
                    '-stroke',
                    '#000C',
                    '-pointsize',
                    "160",
                    '-strokewidth',
                    '2',
                    '-annotate',
                    '0',
                    exposure_val,
                    '-stroke',
                    'none',
                    '-pointsize',
                    "160",
                    '-fill',
                    'white',
                    '-annotate',
                    '0',
                    exposure_val,
                    cur_dest
                ]

                subprocess.run(exposure_script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cur_src=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file
                cur_dest=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file

            # File Name Annotation
            if 'target' in annotations:
                target=image_url
                target_script = [
                    'convert',
                    cur_src,
                    '-gravity',
                    'NorthWest',
                    '-stroke',
                    '#000C',
                    '-pointsize',
                    "160",
                    '-strokewidth',
                    '2',
                    '-annotate',
                    '0',
                    target,
                    '-stroke',
                    'none',
                    '-pointsize',
                    "160",
                    '-fill',
                    'white',
                    '-annotate',
                    '0',
                    target,
                    cur_dest
                ]

                subprocess.run(target_script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cur_src=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file
                cur_dest=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file
           
            # Weather Annotation
            if 'weather' in annotations:
                
                weather = getWeather()

                moon_percent= str(round((int(weather["moonday"]) / 29) * 100)) + '%'
                weather_string = ' Moon:' + moon_percent + \
                    ' Hum:' + weather["humidity"] + \
                    ' ' + weather["temperature"] + \
                    ' ' + weather["condition"]

                weather_script = [
                    'convert',
                    cur_src,
                    '-gravity',
                    'NorthEast',
                    '-stroke',
                    '#000C',
                    '-pointsize',
                    "160",
                    '-strokewidth',
                    '2',
                    '-annotate',
                    '0',
                    weather_string,
                    '-stroke',
                    'none',
                    '-pointsize',
                    "160",
                    '-fill',
                    'white',
                    '-annotate',
                    '0',
                    weather_string,
                    cur_dest
                ]

                subprocess.run(weather_script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cur_src=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file
                cur_dest=current_app.config['BASE_IMAGE_DIRECTORY'] + dest_file
        return await returnResponse({ "annotated_image_url": dest_file }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)