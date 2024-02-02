import trio
from src.logger.logger import Logger
import re
from dataclasses import dataclass, field
from typing import List, Protocol, Generic, TypeAlias, Union, TypeVar, Optional
from enum import Enum, auto


class Gphoto2DeviceCapabilities():
    log: Logger
    can_download: bool
    can_delete: bool
    can_upload: bool
    can_capture: bool
    has_wifi: bool
    all_capabilities: list[str]

    def __init__(self):
        self.log = Logger(__name__)

    def set_capabilities(self, c: list[str]):
        self.can_download = bool('File Download' in c)
        self.can_delete = bool('File Deletion' in c)
        self.can_upload = bool('File Upload' in c)
        # FIXME: This shouldnt be static, only works with Canon EOS cameras
        self.can_capture = bool(
            ['Image Capture', 'Canon EOS Capture', 'Canon EOS Capture 2'])
        self.has_wifi = bool('Canon Wifi support' in c)
        self.all_capabilities = c


class UsbDevice():
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
    id: str
    label: str
    readonly: bool
    type: Gphoto2DeviceConfigType
    current: str
    options: list[str]

    def __init__(self, id: str, label: str, ctype: Gphoto2DeviceConfigType, options: list[str], readonly: bool, current: int):
        self.id = id
        self.label = label
        self.type = Gphoto2DeviceConfigType
        self.options = options
        self.current = current
        self.readonly = readonly


async def create_gphoto2device(**args):
    d = Gphoto2Device(**args)
    await d._init()
    return d


class Gphoto2Device(Gphoto2DeviceCapabilities):
    log: Logger
    camera: UsbDevice
    role: Gphoto2DeviceRole
    config: [Gphoto2DeviceConfig]
    _cmd_prefix: str

    def __init__(self, camera: UsbDevice, role: Gphoto2DeviceRole):
        self.log = Logger(__name__)
        self._cmd_prefix = f'gphoto2 --camera "{camera.model}" --port "{camera.port}"'
        self.camera = camera
        self.role = role

    async def _init(self):
        assert self.camera is not None

        '''
        [CONFIGURATION]
        '''
        try:
            cmd = f'{self._cmd_prefix} --list-all-config'
            _proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
            proc = _proc.stdout.decode().split('\n')
            config_list = []
            _config_list = []
            tmp = []

            # Split lines into a list of config lines lists
            for c in proc:
                if (c == 'END'):
                    _config_list.append(tmp)
                    tmp = []
                else:
                    tmp.append(c)

            for c in _config_list:

                options = [re.sub(r"^Choice: \d+ ", "", s.strip())
                           for s in c[5::]]

                config_list.append(Gphoto2DeviceConfig(
                    id=c[0],
                    label=c[1].removeprefix('Label: '),
                    ctype=c[3].removeprefix('Type: '),
                    readonly=int(c[2].removeprefix('Readonly: ')) == 1,
                    current=c[4].removeprefix('Current: '),
                    options=options,
                ))
            self.config = config_list

        except Exception as e:
            self.log.error(e)
            raise

        '''
        [CAPABILITIES]
        '''
        try:
            cmd = f'{self._cmd_prefix} --summary'
            _proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
            proc = _proc.stdout.decode().split('\n')

            # FIXME: Should be a better way to parse this
            cap_start = proc.index('Device Capabilities:') + 1
            cap_end = cap_start + 2
            _capabilities: list[list[str]] = proc[cap_start:cap_end]
            capabilities: list[str] = [item.strip() for sublist in [
                l.split(', ') for l in _capabilities] for item in sublist]
            self.set_capabilities(capabilities)
        except Exception as e:
            self.log.error(e)
            raise

    async def set_config(self, id: str, index: int):
        try:
            c = [x for x in self.config if x.id == id][0]
            cmd = f'{self._cmd_prefix} --set-config-index {c.id}="{index}"'
            await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
            c.current = c.options[index]
        except Exception as e:
            self.log.error(e)
            raise

    def get_config(self, CamSingleConfOpts):
        pass


async def get_available_usb_devices():
    try:
        proc = await trio.run_process(['gphoto2', '--auto-detect'], capture_stdout=True, capture_stderr=True)
        proc_out = proc.stdout.decode().split('\n')
        del proc_out[0:2]
        available_devices = []
        for line in proc_out:
            if (len(line.strip()) > 0):
                device = UsbDevice(
                    model=line[0:31].strip(), port=line[31:].strip())
                available_devices.append(device)
        return available_devices
    except:
        raise