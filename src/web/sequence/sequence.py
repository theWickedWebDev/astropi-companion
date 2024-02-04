from quart import make_response, current_app
from pydantic.v1.utils import deep_update
from typing import Optional, List
from dataclasses import dataclass
import datetime
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
    LUNAR = auto()
    TIMELAPSE = auto()


@dataclass
class SequenceConfigValue():
    id: str
    index: int
    by_value: bool


@dataclass
class SequenceStep():
    name: str
    note: str
    type: SequenceType
    category: SequenceCategory
    frames: int
    interval: str
    start: Optional[str]
    end: Optional[str]
    config: List[SequenceConfigValue]

@dataclass
class Sequence():
    id: str
    name: str
    description: str
    start: str
    steps: List[SequenceStep]
    

DEFAULT_SEQUENCE = {
    "id": None,
    "name": "",
    "description": "",
    "start": "",
    "type": SequenceType.SIMPLE.name,
    "category": SequenceCategory.NONE.name,
    "steps": []
}

DEFAULT_STEP: SequenceStep = {
    "name": "",
    "frames": 0,
    "interval": 0,
    "start": None,
    "end": None,
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
        full_seq_list.append(json.loads(_seq_data))

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
        return await make_response({'sequence': False}, 200)


@blueprint.route('/<id>/steps', methods=['POST'])
async def create_new_sequence_step(id):
    try:
        BASE_SEQUENCES_DIRECTORY = f"{
            current_app.config['BASE_SEQUENCES_DIRECTORY']}"
        return await make_response({'sequence': True}, 200)

    except Exception as e:
        return await make_response({'sequence': False}, 200)
