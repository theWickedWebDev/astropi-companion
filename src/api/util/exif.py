import os
import trio
import subprocess
import json
import ast
from quart import current_app

from src.api.util import fetchWeather, flatten

# Returns all EXIF Tags from an image
async def getExifTags(image) -> dict:
    try:
        r = await trio.run_process(['exiftool', '-j', image], capture_stdout=True, capture_stderr=True)    
        return json.loads(r.stdout.decode())[0]
    except Exception as e:
        print('[ERROR] getExifTags', e)
        return {}

# Retuns formatted list of response headers for image files
async def buildImageHeaders(img_path: str, errors=[]):
    try:
        exif_data = await getExifTags(img_path)
        astroExif = ast.literal_eval(exif_data['UserComment'])
        _headers = {
            "iso": exif_data['ISO'],
            "aperture": exif_data['Aperture'],
            "shutterspeed": exif_data['ShutterSpeedValue'],
            "exposure": exif_data['MeasuredEV'],
            "shootingmode": exif_data['ShootingMode'],
            "exposuremode": exif_data['ExposureMode'],
            "bulb": exif_data['BulbDuration'],
            **astroExif
        }

        if errors:
            _headers['errors'] = ' '.join(errors)

        headers = flatten({'X-' + str(key): val for key, val in _headers.items()})
        return headers
    except Exception as e:
        print('[ERROR] buildImageHeaders', e)
        return {}

# Querys wttr api and returns formatted exif tags
async def getWeatherExifTags():
    try:
        weather = fetchWeather()
        return {
            "root": [
                '-AmbientTemperature=' + str(weather.get('temp_val')),
                '-Humidity=' + str(weather.get('humidity_val')),
            ],
            "userComment": {
                "moonday": str(weather.get('moonday')),
                "moonphase": weather.get('moonphase'),
                "wind": weather.get('wind'),
                "precipitation": weather.get('precipitation'),
                "zenith": weather.get('zenith'),
                "condition": weather.get('condition'),
                "humidity": weather.get('humidity'),
                "temperature": weather.get('temperature'),
            }
        }
    except Exception as e:
        print('[ERROR] getWeatherExifTags', e.args)
        return {
            "root": [],
            "userComment": {}
        }

# Returns formatted target tags
def getTargetTags(target: dict):
    try:
        return {
            "root": ['-Title=' + target['name']],
            "userComment": {
                "title": target['name'],
                "target": target,
                # Replace me with result from plate solving
                "ra": "",
                "dec": ""
            }  
        }
    except Exception as e:
        print('[ERROR] getTargetTags', e)
        return {
            "root": [],
            "userComment": {}
        }

#  Get and add luminance value to exit data
async def getLuminanceTags(image):
    try:
        lum_proc = await trio.run_process([
            'sh',
            current_app.config['SCRIPTS_PATH'] + '/luminance.sh',
            image
        ], capture_stdout=True, capture_stderr=True)
        
        if lum_proc.stdout:
            return {
                'userComment': { "luminance": lum_proc.stdout.decode().replace('\n', '')}
            }
    except Exception as e:
        print('[ERROR] getLuminanceTags', e)
        return {
            "userComment": {}
        }

async def setExif(_tags, _images):
    try:
        if isinstance(_tags, dict):
            # TODO: Remap dict version of tags to array
            # {"ExposureTime": "5" } ==> ['-ExposureTime=5']
            # tags = ["'" + "-" + str(k) + '=' + str(v) + "'" for k,v in _tags.items()]
            tags = []
        else:
            tags = _tags

        images = [_images] if not isinstance(_images, list) else _images
        exif_cmd = ["exiftool", '-overwrite_original_in_place', *tags, *images]
        await trio.run_process(exif_cmd, stdout=subprocess.DEVNULL)
        return
    except Exception as e:
        print('[ERROR] setExif', e)
        return

# Adds all EXIF tags to images
async def appendExif(_images, target):
    images = [_images] if not isinstance(_images, list) else _images

    try:
        weatherTags = await getWeatherExifTags()
        targetTags = getTargetTags(target)
        # FIXME: Luminance should be the same for each image
        # unless this function is used on previously
        # captured images
        luminanceTags = await getLuminanceTags(images[0])
        userCommentTags = {}
        userCommentTags.update(weatherTags.get('userComment', {}))
        userCommentTags.update(targetTags.get('userComment', {}))
        userCommentTags.update(luminanceTags.get('userComment',{}))
        rootTags = weatherTags.get("root", []) + targetTags.get("root", [])
        tags = [*rootTags, '-UserComment=' + str(userCommentTags) ]
        await setExif(tags, images)
        return
    except Exception as e:
        print('[APPEND EXIF ERROR]', e)
        raise