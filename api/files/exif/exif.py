import subprocess
import os
import json
from quart import request, current_app
import trio

from ._blueprint import blueprint
from api.util import returnResponse, fetchWeather
    
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

        # weather = fetchWeather()
        weather = {}

        # fixme
        lum_val = 0

        result = subprocess.run([
            "exiftool",
            '-Title=' + str(title),
            '-AmbientTemperature=' + str((float(weather.get('temperature').replace('°F', ''))-32)*(5/9)) if weather.get('temperature') else "",
            '-Humidity=' + str(float(weather.get('humidity').replace('%', ''))/100) if weather.get('humidity') else '',
            '-UserComment={\
                "title": "' + str(title) + '", \
                "luminance": "' + str(lum_val) + '", \
                "target": { \
                    "id": "' + target_id + '", \
                    "name": "' + target_name + '", \
                    "ra": "' + target_ra + '", \
                    "dec": "' + target_dec + '" \
                }, \
                "moonday": "' + weather.get('moonday') + '", \
                "moonphase": "' + weather.get('moonphase') + '", \
                "wind": "' + weather.get('wind') + '", \
                "precipitation": "' + weather.get('precipitation') + '", \
                "zenith": "' + weather.get('zenith') + '", \
                "condition": "' + weather.get('condition') + '", \
                "humidity": "' + weather.get('humidity') + '", \
                "temperature": "' + weather.get('') + '", \
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


@blueprint.route('/', defaults={'image_url': ''})
@blueprint.route("/<path:image_url>", methods=["GET"])
async def get_exif_data(image_url):
    try:
        image_path = current_app.config['BASE_IMAGE_DIRECTORY'] +  image_url
        r = await trio.run_process(['exiftool', '-j', image_path], capture_stdout=True, capture_stderr=True)    
        exif_data = json.loads(r.stdout.decode())
        return await returnResponse(*exif_data, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)