import trio
from src.logger.logger import Logger
import uuid
from datetime import datetime
import json
from dotenv import load_dotenv
from enum import Enum, auto
import os
from lib.gphoto2 import Gphoto2, UsbDevice, Gphoto2DeviceConfig, Gphoto2DeviceAbilities, parse_list_all_config

load_dotenv('/home/pi/astropi-companion/.env')
BASE_CONFIGURATION_DIRECTORY = os.environ['QUART_BASE_CONFIGURATION_DIRECTORY']
BASE_CUSTOM_CONFIG_FILE = os.environ['QUART_BASE_CUSTOM_CONFIG_FILE']
BASE_IMAGE_DIRECTORY = os.environ['QUART_BASE_IMAGE_DIRECTORY']
PREVIEW_FILENAME = os.environ['QUART_PREVIEW_FILENAME']


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


class CameraRole(Enum):
    PRIMARY = auto()  # Primary capture device
    GUIDE = auto()    # Guide cam


# Used to create a new Gphoto2Device so that
# I can have an asynchonous "__init__"


async def create_camera(**args):
    d = Camera(**args)
    await d._init()
    return d

"""
Main Class shared around the application
Any changes or queries are ran though an
instance of Gphoto2Device
"""


class Camera():
    log: Logger
    camera: UsbDevice
    lensname: str
    role: CameraRole
    config: [Gphoto2DeviceConfig]
    abilities: Gphoto2DeviceAbilities
    gphoto2: Gphoto2

    def __init__(self, camera: UsbDevice, role: CameraRole):
        self.log = Logger(__name__)
        self.camera = camera
        self.role = role

    async def _init(self):
        assert self.camera is not None
        self.log.debug(self.camera)
        self.gphoto2 = Gphoto2(camera=self.camera)

        try:
            config_list, lensname = await self.gphoto2.list_all_config()
            self.lensname = lensname
            self.config = config_list

        except Exception as e:
            self.log.error(e)
            raise

        try:
            abilities = await self.gphoto2.abilities()
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

            custom_conf = {}
            with open(BASE_CUSTOM_CONFIG_FILE, 'r') as f:
                custom_conf = json.loads(f.read())

            if custom is not False:
                self.log.info('Custom configuration change')
                self.log.debug({
                    "config": id,
                    "value": index
                })
                # COMBINE THIS WITH THE WRITE BELOW?
                with open(BASE_CUSTOM_CONFIG_FILE, 'w') as f:
                    custom_conf.update({id: index})
                    f.write(json.dumps(custom_conf, indent=2))
            else:
                # Remove custom exposure
                if custom is False and id == '/main/capturesettings/shutterspeed' and index != "0":
                    self.log.debug('Removing custom exposure config')
                    try:
                        custom_conf.pop('exposure')
                    except Exception as e:
                        print(e)
                        pass
                    self.log.debug(custom_conf)
                with open(BASE_CUSTOM_CONFIG_FILE, 'w') as f:
                    f.write(json.dumps(custom_conf, indent=2))

                # Setting intended config value
                c = [x for x in self.config if x.id == id][0]

                if by_value:
                    await self.gphoto2.set_config_by_value(id=c.id, value=index)
                else:
                    await self.gphoto2.set_config_by_index(id=c.id, index=index)

                c.current = index if by_value else c.options[int(index)]
        except Exception as e:
            self.log.error(e)
            raise

    async def capture_preview(self):
        self.log.info('Capturing preview image')
        try:
            await self.gphoto2.capture_preview(f"{BASE_IMAGE_DIRECTORY}{PREVIEW_FILENAME}.jpg")
            return f"thumb_{PREVIEW_FILENAME}.jpg"
        except Exception as e:
            self.log.error(e)
            raise

    async def capture_bulb(self, name, exposure, postfix):
        self.log.info('Capturing')
        try:
            date = datetime.now().strftime("%m-%d-%Y")
            time = datetime.now().strftime("%H:%M:%S")
            await self.gphoto2.capture_bulb(f"{BASE_IMAGE_DIRECTORY}{name}/{date}/{time}__{postfix}.%C", exposure)
            return f"{name}/{date}/{time}__{postfix}"
        except Exception as e:
            self.log.error(e)
            raise

    async def capture_shutter(self, name, postfix):
        self.log.info('Capturing')
        try:
            date = datetime.now().strftime("%m-%d-%Y")
            time = datetime.now().strftime("%H:%M:%S")
            await self.gphoto2.capture_shutter(f"{BASE_IMAGE_DIRECTORY}{name}/{date}/{time}__{postfix}.%C")
            return f"{name}/{date}/{time}__{postfix}"
        except Exception as e:
            self.log.error(e)
            raise

    async def save_config_file(self, name: str):
        self.log.info('Saving new configuration file')
        try:
            filename = uuid.uuid4()
            self.log.debug(filename)
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

    def get_json_config(self):
        # BULB mode is special is that it needs an exposure amount alongside it
        is_bulb = [x for x in self.config if x.id ==
                   '/main/capturesettings/shutterspeed'][0].current == 'bulb'

        custom_conf = {}
        with open(BASE_CUSTOM_CONFIG_FILE, 'r') as f:
            custom_conf = json.loads(f.read())

        def get_current(x):
            if (x.id == 'exposure'):
                # If BULB mode is configured, load the custom config: exposure
                return custom_conf.get(x.id) if x.id in custom_conf and is_bulb else str(x.current)
            else:
                # If other custom config, load it (no additional custom configs at this time)
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
            # If config is primary, append to primary
            if (c.get('id') in PRIMARY_CONFIG):
                camera_config_primary.append(c)
            else:
                # Otherwise, store the rest in secondary
                camera_config_secondary.append(c)

        return camera_config_primary, camera_config_secondary, camera_config
