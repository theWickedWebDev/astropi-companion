import trio
from quart import current_app
import os
from dotenv import load_dotenv
from src.logger.logger import Logger
import uuid
import re
import json
from dataclasses import dataclass
from enum import Enum, auto

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

'''
Most relevent camera configurations
'''
PRIMARY_CONFIG = [
    '/main/imgsettings/iso',
    '/main/capturesettings/aperture',
    '/main/capturesettings/shutterspeed',
    'exposure',
    '/main/imgsettings/imageformat',
    '/main/imgsettings/whitebalance',
    '/main/capturesettings/autoexposuremode'
]


class Gphoto2DeviceRole(Enum):
    PRIMARY = auto()  # Primary capture device
    GUIDE = auto()    # Guide cam


class Gphoto2DeviceConfigType(Enum):
    RADIO = auto()   # Multiple choice
    TEXT = auto()    # Text field
    TOGGLE = auto()  # on / off


@dataclass
class Gphoto2DeviceAbilities():
    capture_choices: list[str]
    has_config_support: bool
    can_delete_files: bool
    can_delete_all_files: bool
    can_preview_thumbnail: bool
    can_upload: bool


@dataclass
class UsbDevice():
    model: str
    port: str


@dataclass
class Gphoto2DeviceConfig():
    id: str
    label: str
    type: Gphoto2DeviceConfigType
    options: list[str]
    current: str
    readonly: bool

# Used to create a new Gphoto2Device so that
# I can have an asynchonous "__init__"


async def create_gphoto2device(**args):
    d = Gphoto2Device(**args)
    await d._init()
    return d

"""
Main Class shared around the application
Any changes or queries are ran though an
instance of Gphoto2Device
"""


class Gphoto2Device():
    log: Logger
    camera: UsbDevice
    lensname: str
    role: Gphoto2DeviceRole
    config: [Gphoto2DeviceConfig]
    abilities: Gphoto2DeviceAbilities
    _cmd_prefix: str

    def __init__(self, camera: UsbDevice, role: Gphoto2DeviceRole):
        self.log = Logger(__name__)
        # Ensures instance is targetting the correct camera with all calls to Gphoto2
        self._cmd_prefix = f'gphoto2 --camera "{camera.model}" --port "{camera.port}"'
        self.camera = camera
        self.role = role

    async def _init(self):
        assert self.camera is not None

        '''
        [CONFIGURATION]
        FIXME: Should be a better way to parse this
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

            # Iterate through list and generate cleaned up camera configuration
            for c in _config_list:
                if c[0] in IGNORED_CAMERA_CONFIG:
                    continue

                options = [re.sub(r"^Choice: \d+ ", "", s.strip())
                           for s in c[5::]]

                if (c[0] == '/main/status/lensname'):
                    self.lensname = c[4].removeprefix('Current: ')
                else:
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

            load_dotenv('/home/pi/astropi-companion/.env')
            BASE_CUSTOM_CONFIG = os.environ['QUART_BASE_CUSTOM_CONFIG']
            with open(BASE_CUSTOM_CONFIG, 'r') as f:
                custom_conf = json.loads(f.read())

            CUSTOM_EXPOSURE_CONFIGURATION = Gphoto2DeviceConfig(
                id='exposure',
                label="Custom Exposure",
                type=Gphoto2DeviceConfigType.RADIO.name,
                readonly=False,
                current=custom_conf.get('exposure'),
                options=['45', '60', '75', '100', '120', '150', '180', '210', '240',
                         '270', '300', '330', '360', '390', '420', '450', '480', '540'],
            )
            config_list.append(CUSTOM_EXPOSURE_CONFIGURATION)
            self.config = config_list

        except Exception as e:
            self.log.error(e)
            raise

        '''
        [ABILITIES]
        FIXME: Should be a better way to parse this
        '''
        try:
            cmd = f'{self._cmd_prefix} --abilities'
            _proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
            abilities = {}
            tmp_ability = ''
            tmp_abilities = []
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
            self.capture_choices = abilities.get('Capture choices')
            self.has_config_support = abilities.get('Configuration support')
            self.can_delete_all_files = abilities.get(
                'Delete all files on camera')
            self.can_delete_files = abilities.get(
                'Delete selected files on camera')
            self.can_preview_thumbnail = abilities.get(
                'File preview (thumbnail) support')
            self.can_upload = abilities.get('File upload support')
        except Exception as e:
            self.log.error(e)
            raise

    async def set_config(self, id: str, index: int, by_value: bool = True, custom: bool | str = False):
        try:
            self.log.info(
                f"Setting camera config: {id}={index} by_value:{by_value}")
            BASE_CUSTOM_CONFIG = f"{current_app.config['BASE_CUSTOM_CONFIG']}"
            self.log.debug(f"custom: {custom}")

            if custom is not False:
                self.log.info('Custom configuration change')
                self.log.debug({
                    "config": id,
                    "value": index
                })
                with open(BASE_CUSTOM_CONFIG, 'r') as f:
                    custom_conf = json.loads(f.read())
                with open(BASE_CUSTOM_CONFIG, 'w') as f:
                    custom_conf.update({id: index})
                    f.write(json.dumps(custom_conf, indent=2))
            else:
                # Remove custom exposure
                if custom is False and id == '/main/capturesettings/shutterspeed' and index != "0":
                    self.log.debug('Removing custom exposure config')
                with open(BASE_CUSTOM_CONFIG, 'r') as f:
                    custom_conf = json.loads(f.read())
                    try:
                        custom_conf.pop('exposure')
                    except Exception as e:
                        print(e)
                        pass
                    self.log.debug(custom_conf)
                with open(BASE_CUSTOM_CONFIG, 'w') as f:
                    f.write(json.dumps(custom_conf, indent=2))

                # Setting intended config value
                c = [x for x in self.config if x.id == id][0]
                _cmd = f'--set-config-value {c.id}="{index}"' if by_value else f'--set-config-index {c.id}={index}'
                cmd = f'{self._cmd_prefix} {_cmd}'
                self.log.debug(cmd)
                await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
                c.current = index if by_value else c.options[int(index)]
        except Exception as e:
            self.log.error(e)
            raise

    def get_json_config(self):

        BASE_CUSTOM_CONFIG = f"{current_app.config['BASE_CUSTOM_CONFIG']}"
        custom_conf = {}

        is_bulb = [x for x in self.config if x.id ==
                   '/main/capturesettings/shutterspeed'][0].current == 'bulb'

        with open(BASE_CUSTOM_CONFIG, 'r') as f:
            custom_conf = json.loads(f.read())

        def get_current(x):
            if (x.id == 'exposure'):
                return custom_conf.get(x.id) if x.id in custom_conf and is_bulb else str(x.current)
            else:
                return custom_conf.get(x.id) if x.id in custom_conf else str(x.current)

        camera_config = [{
            "id": x.id,
            "label": x.label,
            "readonly": x.readonly,
            "type": x.type,
            "current": get_current(x),
            "options": x.options
        } for x in self.config]

        camera_config_primary = []
        camera_config_secondary = []

        for c in camera_config:
            if (c.get('id') in PRIMARY_CONFIG):
                camera_config_primary.append(c)
            else:
                camera_config_secondary.append(c)
        return camera_config_primary, camera_config_secondary, camera_config

    async def capture_preview(self):
        self.log.info('Capturing preview image')
        try:
            preview_filename = current_app.config.get('PREVIEW_FILENAME')
            cmd = f'{self._cmd_prefix} --capture-preview --filename "{preview_filename}" --force-overwrite'
            self.log.debug(cmd)
            await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
            # TODO: Dont hardcode preview.jpg :/
            return preview_filename \
                .removeprefix(current_app.config.get('BASE_IMAGE_DIRECTORY')) \
                .replace('preview.jpg', 'thumb_preview.jpg')
        except Exception as e:
            self.log.error(e)
            raise

    async def save_config(self, name: str):
        self.log.info('Saving new configuration file')
        try:
            filename = uuid.uuid4()
            self.log.debug(filename)
            BASE_CONFIGURATION_DIRECTORY = f"{current_app.config['BASE_CONFIGURATION_DIRECTORY']}"
            config_file = f"{BASE_CONFIGURATION_DIRECTORY}{filename}.json"
            conf, *_ = self.get_json_config()

            with open(config_file, 'w') as f:
                f.write(json.dumps({
                    "name": name,
                    "lens": self.lensname,
                    "config": [{"key": c.get('id'), "value": c.get('current')} for c in conf]
                }, indent=2))
            self.log.info(f"Config file saved: {config_file}")
            return
        except Exception as e:
            self.log.error(e)
            raise


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
