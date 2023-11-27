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

@blueprint.route("/append/", methods=["POST"])
async def exif_append():
    res = await request.json

    try:
        image_url = res['image']
        title = res['title']
        ra = res['ra']
        dec = res['dec']
    
        if 'target_id' in res.keys():
            target_id = res['target_id']
        else:
            target_id = ''
    
        if 'target_name' in res.keys():
            target_name = res['target_name']
        else:
            target_name = ''
    
        if 'target_ra' in res.keys():
            target_ra = res['target_ra']
        else:
            target_ra = ''
    
        if 'target_dec' in res.keys():
            target_dec = res['target_dec']
        else:
            target_dec = ''


        image_path = current_app.config['BASE_IMAGE_DIRECTORY'] + os.path.dirname(image_url)
        image_name= os.path.splitext(os.path.basename(image_url))[0]
        image_ext= os.path.splitext(os.path.basename(image_url))[1]
        full_image_path= image_path + '/' + image_name + image_ext

        weather = getWeather()

        lum_val = getLuminanceFromUrl(full_image_path)

        result = subprocess.run([
            "exiftool",
            '-Title=' + str(title),
            '-AmbientTemperature=' + str((float(weather["temperature"].replace('°F', ''))-32)*(5/9)),
            '-Humidity=' + str(float(weather["humidity"].replace('%', ''))/100),
            '-UserComment={\
                "title": "' + str(title) + '", \
                "luminance": "' + str(lum_val) + '", \
                "target": { \
                    "id": "' + target_id + '", \
                    "name": "' + target_name + '", \
                    "ra": "' + target_ra + '", \
                    "dec": "' + target_dec + '" \
                }, \
                "moonday": "' + weather["moonday"] + '", \
                "moonphase": "' + weather['moonphase'] + '", \
                "wind": "' + weather['wind'] + '", \
                "precipitation": "' + weather['precipitation'] + '", \
                "zenith": "' + weather['zenith'] + '", \
                "condition": "' + weather['condition'] + '", \
                "humidity": "' + weather['humidity'] + '", \
                "temperature": "' + weather['temperature'] + '", \
                "ra": "' + ra + '", \
                "dec": "' + dec + '" \
            }',
            full_image_path
        ], capture_output=True, text=True, universal_newlines=True)
        subprocess.run(['rm', full_image_path + '_original'])
        r = subprocess.Popen(['exiftool', '-j', full_image_path], stdout=subprocess.PIPE)
        jr = r.stdout.read()
        j = jr.decode('utf8').replace("'", '"')
        data = json.loads(j)

        data[0]['UserComment'] = json.loads(data[0]['UserComment'])

        return await returnResponse({ "success": True, "data": data }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)
