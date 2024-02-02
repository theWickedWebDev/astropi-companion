from copy import deepcopy
import json

LAST_CAMERA_SETTINGS = '/tmp/astro.camera-settings.tmp'


def configOption(v, i): return {"value": v, "index": i}


ISO = {
    "_config": "iso",
    "_default": "800",
    "Auto": configOption("Auto", 0),
    "100": configOption("100", 1),
    "200": configOption("200", 2),
    "400": configOption("400", 3),
    "800": configOption("800", 4),
    "1600": configOption("1600", 5),
    "3200": configOption("3200", 6),
    "6400": configOption("6400", 7)
}

AEB = {
    "_config": "aeb",
    "_default": "off",
    'Off': configOption("off", 0)
}

DRIVE_MODE = {
    "_config": "drivemode",
    "_default": "0",
    '0': configOption("Single", 0),
    '2': configOption("Single", 3),
    '10': configOption("Single", 2)
}

AUTO_EXPOSURE_MODE = {
    "_config": "autoexposuremode",
    "_default": "Manual",
    "MANUAL": configOption("Manual", 3),
    "APERTURE_PRIORITY": configOption("AV", 2),
}

IMAGE_FORMAT = {
    "_config": "imageformat",
    "_default": "RAW + Large Fine JPEG",
    "LG_FINE_JPG": configOption("Large Fine JPEG", 0),
    "LG_JPG": configOption("Large Normal JPEG", 1),
    "MD_FINE_JPG": configOption("Medium Fine JPEG", 2),
    "MD_JPG": configOption("Medium Normal JPEG", 3),
    "SM_FINE_JPG": configOption("Small Fine JPEG", 4),
    "SM_JPG": configOption("Small Normal JPEG", 5),
    "RAW+JPG": configOption("RAW + Large Fine JPEG", 6),
    "RAW": configOption("RAW", 7),
}

PICTURE_STYLE = {
    "_config": "picturestyle",
    "_default": "Standard",
    "STANDARD": configOption("Standard", 0),
}

SHUTTERSPEEDS = {
    30: "30",
    25: "25",
    20: "20",
    15: "15",
    13: "13",
    10.3: "10.3",
    8: "8",
    6.3: "6.3",
    5: "5",
    4: "4",
    3.2: "3.2",
    2.5: "2.5",
    2: "2",
    1.6: "1.6",
    1.3: "1.3",
    1: "1",
    0.8: "0.8",
    0.6: "0.6",
    0.5: "0.5",
    0.4: "0.4",
    0.3: "0.3",
    1/4: "1/4",
    1/5: "1/5",
    1/6: "1/6",
    1/8: "1/8",
    1/10: "1/10",
    1/13: "1/13",
    1/15: "1/15",
    1/20: "1/20",
    1/25: "1/25",
    1/30: "1/30",
    1/40: "1/40",
    1/50: "1/50",
    1/60: "1/60",
    1/80: "1/80",
    1/100: "1/100",
    1/125: "1/125",
    1/160: "1/160",
    1/200: "1/200",
    1/250: "1/250",
    1/320: "1/320",
    1/400: "1/400",
    1/500: "1/500",
    1/640: "1/640",
    1/800: "1/800",
    1/1000: "1/1000",
    1/1250: "1/1250",
    1/1600: "1/1600",
    1/2000: "1/2000",
    1/2500: "1/2500",
    1/3200: "1/3200",
    1/4000: "1/4000"
}

SETTING_OPTIONS = [ISO, AEB, AUTO_EXPOSURE_MODE,
                   IMAGE_FORMAT, PICTURE_STYLE, DRIVE_MODE]

DEFAULT_CAMERA_SETTINGS_KEYS = [
    "iso",
    "shutterspeed",
    "imageformat",
    "picturestyle",
    "autoexposuremode",
    'aeb',
    'drivemode'
]

EMPTY_CAMERA_SETTINGS_DICT = {
    k: None for k in DEFAULT_CAMERA_SETTINGS_KEYS
}

CAMERA_SETTINGS_DICT_DEFAULTS = {
    k['_config']: k['_default'] for k in SETTING_OPTIONS
}

CAMERA_SETTINGS_DICT_BY_NAME = {
    k['_config']: k for k in SETTING_OPTIONS
}


def generateCameraConfigDict(values={}):
    errors = []
    settings = deepcopy(CAMERA_SETTINGS_DICT_DEFAULTS)
    for key, value in values.items():
        if key not in DEFAULT_CAMERA_SETTINGS_KEYS:
            errors.append('[' + key + '] property not found')
            continue
        try:
            if key == 'shutterspeed':
                if float(value) > 10 or float(value) == 0:
                    settings['shutterspeed'] = 'bulb'
                    settings['exposure'] = str(int(value)) + 's'
                else:
                    try:
                        v = list(SHUTTERSPEEDS.items())[-1][1]
                        for x in SHUTTERSPEEDS.keys():
                            if float(value) >= x:
                                v = SHUTTERSPEEDS[x]
                                break
                        settings['shutterspeed'] = str(v)
                    except Exception as e:
                        print(e)
            else:
                settings[key] = CAMERA_SETTINGS_DICT_BY_NAME[key][value]['value']
        except Exception as e:
            errors.append('[' + key + ': ' + value + '] not applied')

    with open(LAST_CAMERA_SETTINGS, 'w') as convert_file:
        convert_file.write(json.dumps(settings))
    return settings, errors
