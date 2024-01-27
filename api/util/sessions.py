from quart import current_app
from datetime import datetime
import json
import os
from pydantic.v1.utils import deep_update
from astropy import units as u
from astropy.coordinates import SkyCoord

from api.util import DEFAULT_LIGHT_FRAMES_COUNT, DEFAULT_FLAT_FRAMES_COUNT, DEFAULT_DARK_FRAMES_COUNT
from enum import Enum

class Statuses(Enum):
    CREATED = 'CREATED'
    COMPLETED = 'COMPLETED'
    EXPIRED = 'EXPIRED'

EMPTY_SESSION_DATA = {
    "id": None,
    "modified_time": None,
    "status": Statuses.CREATED.value,
    "frames": {
        "required": {
            "lights": DEFAULT_LIGHT_FRAMES_COUNT,
            "darks": DEFAULT_DARK_FRAMES_COUNT,
            "flats": DEFAULT_FLAT_FRAMES_COUNT
        },
        "captured": {
            "lights": 0,
            "darks": 0,
            "flats": 0
        },
        "lights": {},
        "darks": {},
        "flats": {}
    },
    "camera": {
        "config": {
            "iso": "800",
            "aeb": "Off",
            "drivemode": "0",
            "autoexposuremode": "MANUAL",
            "imageformat": "RAW+JPG",
            "picturestyle": "Standard",
            "shutterspeed": 30
        },
        "lens": {
            "name": None,
            "aperture": None,
            "focal_length": None
        }
    },
    "details": {
        "name": None,
        "description": None,
        "scheduled_start": None,
        "timeUntilEvent": None
    },
    "target": {}
}

CALIBRATION_CAMERA_SETTINGS = {
    "iso": "3200",
    "aeb": "Off",
    "autoexposuremode": "MANUAL",
    "imageformat": "LG_FINE_JPG",
    "picturestyle": "STANDARD",
    "drivemode": "0",
    "shutterspeed": "4",
    "aperture": "5.6"
}

def session_exists(id):
    BASE_SESSIONS_DIRECTORY = f"{current_app.config['BASE_SESSIONS_DIRECTORY']}"
    return os.path.isfile(f"{BASE_SESSIONS_DIRECTORY}{id}.json")

def read_session_file(p) -> json:
    data = {}
    with open(p, 'r') as f:
        data = f.read()
    return json.loads(data)

def appendGeneratedData(p, d={}) -> dict:
    modified_time = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%A, %B %d, %Y %I:%M:%S")
    data = deep_update(read_session_file(p), d)
    
    try:
        timeUntil = None
        scheduled_start = data.get('details', {}).get('scheduled_start', None)
        if (scheduled_start):
            start_time = datetime.fromisoformat(scheduled_start)
            c = start_time - datetime.now()
            days = divmod(c.total_seconds(), 60*60*24) 
            hours = divmod(days[1], 60*60)
            minutes = divmod(hours[1], 60)
            timeUntil = {
                "days": int(days[0]),
                "hours": int(hours[0]),
                "mins": int(minutes[0])
            }
            data = deep_update(data, {
                "modified_time": modified_time,
                "details": {
                    "timeUntilEvent": timeUntil
                }
            })

    except Exception as e:
        print(e)
    
    return data

def deep_update_session(file, data) -> dict:
    d = deep_update(appendGeneratedData(file), data)

    with open(file, 'w') as f:         
        f.write(json.dumps(d, indent=2))

    return d

def get_session_data(file) -> json:
    with open(file, 'r') as f:
        res =f.read()
    return json.loads(res)

