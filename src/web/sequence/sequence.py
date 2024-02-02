from quart import make_response, current_app
from pydantic.v1.utils import deep_update
import glob
import json
import uuid
import os
from ._blueprint import blueprint
from enum import Enum, auto


class SequenceType(Enum):
    SIMPLE = auto()
    SCHEDULED = auto()


class SequenceCategory(Enum):
    NONE = auto()
    DSO = auto()
    PLANETARY = auto()
    SOLAR = auto()


DEFAULT_SEQUENCE = {
    "name": "",
    "type": SequenceType.SIMPLE.name,
    "category": SequenceCategory.NONE.name,
    "frames": 0,
    "interval": 0,
    "start": 0,
    "end": 0,
    "config": {}
}


def get_sequences():
    BASE_SEQUENCES_DIRECTORY = f"{
        current_app.config['BASE_SEQUENCES_DIRECTORY']}"

    seq_list = glob.glob(BASE_SEQUENCES_DIRECTORY + '*', recursive=True)
    full_seq_list = []

    for s in seq_list:
        _seq_data = {}
        with open(s, 'r') as f:
            _seq_data = f.read()

        _data = {}
        _data.update(json.loads(_seq_data))
        _data.update({"id": s.removeprefix(
            BASE_SEQUENCES_DIRECTORY).removesuffix('.json')})
        full_seq_list.append(_data)

    return full_seq_list


@blueprint.route('/', methods=['POST'])
async def create_new_sequence():
    try:
        BASE_SEQUENCES_DIRECTORY = f"{
            current_app.config['BASE_SEQUENCES_DIRECTORY']}"

        sequence_id = str(uuid.uuid4())
        new_seq_file = f"{BASE_SEQUENCES_DIRECTORY}{sequence_id}.json"

        if not os.path.isfile(new_seq_file):
            new_seq_data = DEFAULT_SEQUENCE

            with open(new_seq_file, 'w') as f:
                f.write(json.dumps(new_seq_data, indent=2))
            return await make_response(new_seq_data, 200)
        else:
            return await make_response({}, 400)

    except Exception as e:
        print('\n')
        print(e)
        print('\n')
        return await make_response({'sequence': False}, 200)


@blueprint.route('/<id>/steps', methods=['POST'])
async def create_new_sequence_step(id):
    try:
        BASE_SEQUENCES_DIRECTORY = f"{
            current_app.config['BASE_SEQUENCES_DIRECTORY']}"

        print('\n BASE_SEQUENCES_DIRECTORY')
        print(BASE_SEQUENCES_DIRECTORY)
        print('ID')
        print(id)
        print('\n')
        return await make_response({'sequence': True}, 200)

    except Exception as e:
        print('\n')
        print(e)
        print('\n')
        return await make_response({'sequence': False}, 200)
