import os
import trio
import json
import ast
from quart import current_app

from capture_app.util import fetchWeather, flatten

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
        weather = await fetchWeather()
        return {
            "root": [
                '-AmbientTemperature=' + str(weather['temp_val']),
                '-Humidity=' + str(weather['humidity_val']),
            ],
            "userComment": {
                "moonday": weather["moonday"],
                "moonphase": weather['moonphase'],
                "wind": weather['wind'],
                "precipitation": weather['precipitation'],
                "zenith": weather['zenith'],
                "condition": weather['condition'],
                "humidity": weather['humidity'],
                "temperature": weather['temperature'],
            }
        }
    except Exception as e:
        print('[ERROR] fetchWeather', e)
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
        print('[ERROR] target', e)
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
        print('[ERROR] luminance', e)
        return {
            "userComment": {}
        }

async def setExif(_tags, _images):
    try:
        if isinstance(_tags, dict):
            # TODO: Remap dict version of tags to array
            # {"ExposureTime": "5" } ==> ['-ExposureTime=5']
            # tags = ["'" + "-" + str(k) + '=' + str(v) + "'" for k,v in _tags.items()]
            # userComment = "-UserComment='" + str(_tags['UserComment']) + "'"
            # title = "-UserComment='" + str(_tags['UserComment']) + "'"
            # humidity = "-UserComment='" + str(_tags['UserComment']) + "'"
            # tags = [userComment]
            tags = []
        else:
            tags = _tags

        images = [_images] if not isinstance(_images, list) else _images
        exif_cmd = ["exiftool", '-overwrite_original_in_place', *tags, *images]
        return await trio.run_process(exif_cmd, capture_stdout=True, capture_stderr=True)
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
        userCommentTags.update(weatherTags['userComment'])
        userCommentTags.update(targetTags['userComment'])
        userCommentTags.update(luminanceTags['userComment'])
        rootTags = weatherTags['root'] + targetTags['root']
        tags = [*rootTags, '-UserComment=' + str(userCommentTags) ]
        await setExif(tags, images)
        return
    except Exception as e:
        print('[APPEND EXIF ERROR]', e)
        raise