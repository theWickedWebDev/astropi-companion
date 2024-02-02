import trio
from src.logger.logger import Logger
from dataclasses import dataclass, field
from typing import List, Protocol, Generic, TypeAlias, Union, TypeVar
from enum import Enum, auto


# class AEB(CamSingleConfOpts):
#     OFF = 0
#     ONE_THIRD = auto()
#     TWO_THIRDS = auto()
#     ONE = auto()
#     ONE_ONE_THIRD = auto()
#     ONE_TWO_THIRDS = auto()
#     TWO = auto()


class Device():
    model: str
    port: str

    def __init__(self, model: str, port: str):
        self.model = model
        self.port = port


class Gphoto2DeviceRole(Enum):
    PRIMARY = auto()
    GUIDE = auto()


class Gphoto2DeviceConfigType(Enum):
    RADIO = auto()
    TEXT = auto()
    TOGGLE = auto()


class Gphoto2DeviceConfig():
    config: str
    label: str
    readonly: bool
    type: Gphoto2DeviceConfigType
    current: str
    options: list(Enum)

    def __init__(self, id: str, label: str, ctype: Gphoto2DeviceConfigType, options: set[str], readonly: bool, current: int, default: int):
        self.id = id
        self.label = label
        self.type = Gphoto2DeviceConfigType
        self.options = options
        self.current = current
        self.default = default
        self.readonly = readonly

    def set_config(self, CamSingleConfOpts):
        pass

    def get_config(self, CamSingleConfOpts):
        pass


async def create_gphoto2device(**kwargs):
    d = Gphoto2Device(**kwargs)
    await d._init()
    return d


class Gphoto2Device():
    log: Logger
    camera: Device
    role: Gphoto2DeviceRole
    config: [Gphoto2DeviceConfig]
    can_capture: bool
    can_download: bool
    can_upload: bool
    _cmd_prefix: str

    def __init__(self, camera: Device, role: Gphoto2DeviceRole, config: [Gphoto2DeviceConfig]):
        self.log = Logger(__name__)
        self._cmd_prefix = f'gphoto2 --camera "{camera.model}" --port "{camera.port}"'
        self.config = config
        pass

    async def _init(self):
        assert self.camera.model is not None
        cmd = f'{self._cmd_prefix} --summary'
        try:
            proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
            proc_out = proc.stdout.decode()
            self.log.json(proc_out)
        except Exception as e:
            self.log.error(e)
            raise
