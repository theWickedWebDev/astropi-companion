from quart import current_app
from pydantic.v1.utils import deep_update
import os
import json
from enum import Enum


class TelescopeControlMethods(Enum):
    GOTO = 'goto'
    CALIBRATE = 'calibrate'


class TelescopeTargetTypes(Enum):
    RA_DEC = 'RA_DEC'
    SOLAR_SYSTEM = 'SOLAR_SYSTEM'
    BY_NAME = 'BY_NAME'


class Telescope():
    def __init__(self, _type: TelescopeTargetTypes):
        self.type = _type


def read_telescope_file():
    telescope_file = current_app.config['BASE_TELESCOPE_JSON']
    data = {}
    if not os.path.isfile(telescope_file):
        with open(telescope_file, 'w') as f:
            f.write(json.dumps({}, indent=2))

    with open(telescope_file, 'r') as f:
        data = f.read()

    return json.loads(data)


def deep_update_telescope_file(data) -> dict:
    telescope_file = current_app.config['BASE_TELESCOPE_JSON']
    d = deep_update(read_telescope_file(), data)

    with open(telescope_file, 'w') as f:
        f.write(json.dumps(d, indent=2))

    return d
