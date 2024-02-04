import trio
import os
from src.logger.logger import Logger
from dotenv import load_dotenv
import json
from dataclasses import dataclass
from enum import Enum, auto
import re

load_dotenv('/home/pi/astropi-companion/.env')
BASE_CUSTOM_CONFIG = os.environ['QUART_BASE_CUSTOM_CONFIG_FILE']


@dataclass
class UsbDevice():
    model: str
    port: str


@dataclass
class Gphoto2DeviceAbilities():
    capture_choices: list[str]
    has_config_support: bool
    can_delete_files: bool
    can_delete_all_files: bool
    can_preview_thumbnail: bool
    can_upload: bool


class Gphoto2DeviceConfigType(Enum):
    RADIO = auto()   # Multiple choice
    TEXT = auto()    # Text field
    TOGGLE = auto()  # on / off


@dataclass
class Gphoto2DeviceConfig():
    id: str
    label: str
    type: Gphoto2DeviceConfigType
    options: list[str]
    current: str
    readonly: bool


"""
Camera configuration that doesnt really
apply to this application
"""
IGNORED_CAMERA_CONFIG = [
    '/main/status/vendorextension',
    '/main/other/',
    '/main/settings/datetime',
    '/main/actions/uilock',
    '/main/actions/popupflash',
    '/main/actions/opcode',
    '/main/settings/customfuncex',
    '/main/settings/focusinfo',
    '/main/settings/flashcharged',
    '/main/settings/eventmode',
    '/main/status/ptpversion',
    '/main/status/Battery Level',
    '/main/capturesettings/exposurecompensation',
    '/main/capturesettings/storageid',
    '/main/other/d406',
    '/main/other/d402',
    '/main/other/d407',
    '/main/other/d303',
    '/main/settings/autopoweroff',
    '/main/settings/depthoffield',
    '/main/settings/capture',
    '/main/actions/eoszoom',
    '/main/actions/eoszoomposition',
    '/main/settings/movierecordtarget',
    '/main/settings/strobofiring',
    '/main/capturesettings/meteringmode',
    '/main/status/eosserialnumber',
    '/main/status/serialnumber',
    '/main/status/eosmovieswitch',
    '/main/settings/remotemode',
    '/main/actions/eosmoviemode',
    '/main/settings/output',
    '/main/capturesettings/bracketmode',
    '/main/status/model'
]


def parse_list_all_config(proc):
    lensname = ''
    shutterspeed = ''
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

    # Iterate through list and generate cleaned up camera configuration
    for c in _config_list:
        if c[0] in IGNORED_CAMERA_CONFIG:
            continue

        options = [re.sub(r"^Choice: \d+ ", "", s.strip())
                   for s in c[5::]]

        # Save value of lensname before dropping it
        if (c[0] == '/main/status/lensname'):
            lensname = c[4].removeprefix('Current: ')
        else:
            if (c[0] == '/main/capturesettings/shutterspeed'):
                shutterspeed = c[4].removeprefix('Current: ')

            config_list.append(Gphoto2DeviceConfig(
                id=c[0],
                label=c[1].removeprefix('Label: '),
                type=c[3].removeprefix('Type: '),
                readonly=int(c[2].removeprefix('Readonly: ')
                             ) == 1 or '/main/status/' in c[0],
                current=c[4].removeprefix('Current: '),
                options=options,
            ))
    '''
    [CUSTOM CONFIGURATION]
    FIXME: Prob a better way to do this
    These configurations are not handled by gphoto2 but are specific
    to this application only
    '''

    with open(BASE_CUSTOM_CONFIG, 'r') as f:
        custom_conf = json.loads(f.read())

    CUSTOM_EXPOSURE_CONFIGURATION = Gphoto2DeviceConfig(
        id='exposure',
        label="Custom Exposure",
        type=Gphoto2DeviceConfigType.RADIO.name,
        readonly=False,
        current=custom_conf.get(
            'exposure') if shutterspeed == 'bulb' else None,
        options=['45', '60', '75', '100', '120', '150', '180', '210', '240',
                 '270', '300', '330', '360', '390', '420', '450', '480', '540'],
    )
    config_list.append(CUSTOM_EXPOSURE_CONFIGURATION)

    return config_list, lensname


async def get_available_usb_devices():
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


class Gphoto2():
    log: Logger
    _prefix: str

    def __init__(self, camera: UsbDevice):
        self.log = Logger(__name__)
        # Ensures instance is targetting the correct camera with all calls to Gphoto2
        self._prefix = f'gphoto2 --camera "{camera.model}" --port "{camera.port}"'
        self.log.debug(camera.__dir__)

    async def list_all_config(self):
        cmd = f'{self._prefix} --list-all-config'
        _proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
        proc = _proc.stdout.decode().split('\n')
        config_list, lensname = parse_list_all_config(proc)
        return config_list, lensname

    async def abilities(self):
        cmd = f'{self._prefix} --abilities'
        _proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)

        tmp_ability = ''
        tmp_abilities = []
        abilities = {}

        for l in _proc.stdout.decode().split('\n')[2::]:
            a = [ll.strip() for ll in l.split(':')]
            if (len(a) != 2):
                continue
            if (a[0] != '' and a[1] == ''):
                tmp_ability = a[0]
            elif (a[0] != '' and a[1] != ''):
                abilities.update({a[0]: a[1]})
            else:
                tmp_abilities.append(a[1])

            abilities.update({tmp_ability: tmp_abilities})

        return abilities

    async def set_config_by_index(self, id: str, index: str):
        _cmd = f'--set-config-index {id}={index}'
        cmd = f'{self._prefix} {_cmd}'
        await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)

    async def set_config_by_value(self, id: str, value: str):
        _cmd = f'--set-config-value {id}="{value}"'
        cmd = f'{self._prefix} {_cmd}'
        await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)

    async def capture_preview(self, filename=str):
        cmd = f'{self._prefix} --capture-preview --filename "{filename}" --force-overwrite'
        self.log.debug(cmd)
        await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)

    async def capture_bulb(self, filename: str, exposure: str):
        # TODO: Add hook for annotations/luminocity/platesolve/etc..
        cmd = f'{self._prefix} --filename "{filename}" --set-config eosremoterelease=5 --wait-event={exposure}s --set-config eosremoterelease=11 --wait-event-and-download="CAPTURECOMPLETE"'
        self.log.debug(cmd)
        _proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
        proc = _proc.stdout.decode().split('\n')
        self.log.debug(proc)

    async def capture_shutter(self, filename: str):
        # TODO: Add hook for annotations/luminocity/platesolve/etc..
        # --frames 3
        cmd = f'{self._prefix} --filename "{filename}" --capture-image-and-download'
        self.log.debug(cmd)
        _proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
        proc = _proc.stdout.decode().split('\n')
        self.log.debug(proc)
