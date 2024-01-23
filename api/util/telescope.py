from quart import current_app
from pydantic.v1.utils import deep_update
import os
import json


def read_telescope_file() -> json:
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