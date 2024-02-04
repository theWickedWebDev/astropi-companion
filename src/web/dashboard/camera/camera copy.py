import trio
from quart import make_response, jsonify, current_app
from dataclasses import dataclass, field
from typing import List, Protocol, TypeAlias
from src.logger.logger import Logger 
from enum import Enum, auto
import itertools
import datetime
import re
from ._blueprint import blueprint
from . import config
from ..util.capture import capturePhoto
from ..util.camera_config import generateCameraConfigDict

class ConfigName(Enum):
    APERTURE = "/main/capturesettings/aperture"
    SHUTTERSPEED = "/main/capturesettings/shutterspeed"
    ISO = "/main/imgsettings/iso"
    IMAGEFORMAT = "/main/imgsettings/imageformat"
    PICTURESTYLE = "/main/capturesettings/picturestyle"
    AEB = "/main/capturesettings/aeb"
    FOCUSMODE = "/main/capturesettings/focusmode"
    AUTOEXPOSUREMODE = "/main/capturesettings/autoexposuremode"
    DRIVEMODE = "/main/capturesettings/drivemode"
    METERINGMODE ="/main/capturesettings/meteringmode"
    WHITEBALANCE = "/main/imgsettings/whitebalance"
    COLORSPACE = "/main/imgsettings/colorspace"
    FOCUSDRIVE = "/main/actions/manualfocusdrive"
    REMOTERELEASE = "/main/actions/eosremoterelease"
    REVIEWTIME = "/main/settings/reviewtime"
    EVFMODE = "/main/settings/evfmode"
    AUTOPOWEROFF = "/main/settings/autopoweroff"
    CAPTURETARGET = "/main/settings/capturetarget"
    CAMERAMODEL = "/main/status/cameramodel"
    BATTERYLEVEL = "/main/status/batterylevel"
    LENSNAME = "/main/status/lensname"

@dataclass(init=True)
class SetConfig:
    name: ConfigName
    value: str


class VendorCaptures(Enum):
    CANONEOSCAPTURE = "Canon EOS Capture"
    CANONEOSCAPTURE2 = "Canon EOS Capture 2"

class CameraCapabilities(Enum):
    NODOWNLOAD      = "No File Download"
    DOWNLOAD        = "File Download"
    NODELETION      = "No File Deletion"
    DELETION        = "File Deletion"
    NOUPLOAD        = "No File Upload"
    UPLOAD          = "File Upload"
    NOCAPTURE       = "No Image Capture"
    CAPTURE         = "Image Capture"
    NOVENDORCAPTURE = "No vendor specific capture" # TODO: Check me, Canon EOS Capture | Canon EOS Capture 2
    VENDORCAPTURE   = VendorCaptures
    NOOPENCAPTURE   = "No Open Capture"
    OPENCAPTURE     = "Open Capture"


class CameraType(Enum):
    PRIMARY = auto()
    GUIDE = auto()


class CameraConfigType(Enum):
    RADIO = auto()
    TEXT = auto()
    TOGGLE = auto()


@dataclass(init=True)
class CameraDevice:
    port: str
    model: str


@dataclass(init=True)
class CameraConfig:
    config: ConfigName
    label: str
    readonly: bool
    type: CameraConfigType
    current: str
    options: List[str]


class CameraConfigValue(Protocol):
    label: str
    value: str


class CameraConfigs(Protocol):
    actions: List[CameraConfig]
    capture: List[CameraConfig]
    other: List[CameraConfig]
    status: {
        "batterylevel": CameraConfigValue,
        "cameramodel": CameraConfigValue
    }


class CameraBase():
    _log: Logger
    mocked: bool = False
    available_devices: List[CameraDevice] = None
    device: CameraDevice = None
    capabilities: List[CameraCapabilities] = []
    canCapture: bool = False
    canDownload: bool = False

    def __init__(self, mocked: bool = False):
        self._log = Logger(__name__)
        self._log.info("Creating Camera")
        self.mocked = mocked


    async def init(self):
        self._log.info("Getting Available Devices")
        await self._get_available_devices()


    async def _get_available_devices(self):
        proc = await trio.run_process(['gphoto2', '--auto-detect'], capture_stdout=True, capture_stderr=True)
        proc_out = proc.stdout.decode().split('\n')
        del proc_out[0:2]
        available_devices = []
        for line in proc_out:
            if (len(line.strip()) > 0):
                device = CameraDevice(model=line[0:31].strip(), port=line[31:].strip())
                available_devices.append(device)    
        if (proc.stderr):
            self._log.error(proc.stderr)   
        self.available_devices = available_devices    
        return available_devices


    async def auto_detect(self):
        try:
            assert self.available_devices is not None
        except AssertionError as e:
            await self._get_available_devices()
        self._log.debug('Using ' + self.available_devices[0].model)
        await self.set_device(self.available_devices[0])


    async def set_device(self, device: CameraDevice):
        try:
            assert isinstance(device, CameraDevice)
            self.device = device
            await self.summary()
            if (CameraCapabilities.CAPTURE in self.capabilities):
                self.canCapture = True
            for v in VendorCaptures:
                if v in self.capabilities:
                    self.canCapture = True
        except AssertionError as e:
            self._log.error(e)


    async def summary(self):
        try:
            assert self.device.model is not None
            cmd = f'gphoto2 --camera "{self.device.model}" --port "{self.device.port}" --summary'
            try:
                proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
                proc_out = proc.stdout.decode()
                self._log.debug(proc_out)
                if (CameraCapabilities.NOCAPTURE.value in proc_out):
                    self.capabilities.append(CameraCapabilities.NOCAPTURE)
                elif (CameraCapabilities.CAPTURE.value in proc_out):
                    self.capabilities.append(CameraCapabilities.CAPTURE)
                if (CameraCapabilities.NOUPLOAD.value in proc_out):
                    self.capabilities.append(CameraCapabilities.NOUPLOAD)
                elif (CameraCapabilities.UPLOAD.value in proc_out):
                    self.capabilities.append(CameraCapabilities.UPLOAD)
                if (CameraCapabilities.NODOWNLOAD.value in proc_out):
                    self.capabilities.append(CameraCapabilities.NODOWNLOAD)
                elif (CameraCapabilities.DOWNLOAD.value in proc_out):
                    self.capabilities.append(CameraCapabilities.DOWNLOAD)
                if (CameraCapabilities.NODELETION.value in proc_out):
                    self.capabilities.append(CameraCapabilities.NODELETION)
                elif (CameraCapabilities.DELETION.value in proc_out):
                    self.capabilities.append(CameraCapabilities.DELETION)
                if (CameraCapabilities.NOOPENCAPTURE.value in proc_out):
                    self.capabilities.append(CameraCapabilities.NOOPENCAPTURE)
                elif (CameraCapabilities.OPENCAPTURE.value in proc_out):
                    self.capabilities.append(CameraCapabilities.OPENCAPTURE)
                for v in CameraCapabilities.VENDORCAPTURE.value:
                    if (v.value in proc_out ):
                        self.capabilities.append(v)
                if (CameraCapabilities.NOVENDORCAPTURE.value in proc_out):
                    self.capabilities.append(CameraCapabilities.NOVENDORCAPTURE)
                return proc_out
            except Exception as e:
                self._log.error(e.args)
        except Exception as e:
            self._log.error('A camera is not set')


class Camera(CameraBase):
    type: CameraType
    configs: CameraConfigs

    def __init__(self, type: CameraType, **kwargs):
       super().__init__(**kwargs)
       self.type = type

    async def get_config(self):
        cmd = f'gphoto2 --camera "{self.device.model}" --port "{self.device.port}" --list-all-config'
        c_proc = await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
        _config = c_proc.stdout.decode().split('\n')
        capture_config = []
        actions_config = []
        status_config = {}
        other_config = []
        
        tmp_a = []
        tmp_b = []
        for i in _config:
            if (i == "END"):
                tmp_b.append(tmp_a)
                tmp_a = []
                continue
            tmp_a.append(i)
        for i in tmp_b:
            if (i[0] in ConfigName):
                body = CameraConfig(
                    config = ConfigName(i[0].strip()),
                    type = CameraConfigType[i[3].removeprefix('Type: ').strip()],
                    # FIXME: This wont work always.. only with Canon EOS
                    label = i[1].removeprefix('Label: ').replace('Canon ', '').replace('EOS ', '').replace('DSLR ', '').strip(),
                    readonly = i[2].removeprefix('Readonly: ') == "1",
                    current = i[4].removeprefix('Current: ').strip(),
                    options = [re.sub(r"^Choice: \d+ ", "", s.strip()) for s in i[5::]]
                )
                if (i[0] in [
                    ConfigName.APERTURE,
                    ConfigName.SHUTTERSPEED,
                    ConfigName.ISO,
                    ConfigName.IMAGEFORMAT,
                    ConfigName.PICTURESTYLE,
                    ConfigName.AEB,
                    ConfigName.AUTOEXPOSUREMODE
                ]):
                    capture_config.append(body)
                elif (i[0] in [
                    ConfigName.CAMERAMODEL,
                    ConfigName.BATTERYLEVEL,
                    ConfigName.LENSNAME
                ]):
                    status_config.update({
                        body.config.value.split('/')[-1]: CameraConfigValue(
                            label = body.label,
                            value = body.current
                        )
                    })
                elif (i[0] in [
                    ConfigName.FOCUSDRIVE,
                    ConfigName.REMOTERELEASE
                ]):
                    actions_config.append(body)
                else:
                    if (body.config.value == ConfigName.EVFMODE.name):
                        body.label = "Electronic Viewfinder"
                    other_config.append(body)

        configs: CameraConfigs = {
            "capture": capture_config,
            "actions": actions_config,
            "status": status_config,
            "other": other_config
        }

        self._log.json(configs)
        self.configs = configs
        return configs

    def set_config(self, d: [SetConfig]):
        for _d in d:
            self._log.debug(_d)
        return
        # try:
        #     cmd = f'gphoto2 --set-config-index {setting}="{value}"'
        #     await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
        #     return await make_response(jsonify({"success": True}), 200)
        # except Exception as e:
        #     return await make_response(jsonify({"success": False}), 400)

    async def capture(self):
        self._log.info('Capturing Photo')
        try:
            TMP_CALIBRATION_FRAME_LOCATION = f"{
            current_app.config['TMP_CALIBRATION_FRAME_LOCATION']}"

            config = generateCameraConfigDict()
            
            self._log.json(config)

            assert self.canCapture

            imageFormat = config.get('imageformat')

            DEFAULT_FILENAME = datetime.now().strftime("%d-%m-%Y_%H:%M:%S:%f")
            file = DEFAULT_FILENAME  # without extension
            file_name = file + '.%C'  # extention

            remote_file_formatted_name = current_app.config.get(
                "BASE_IMAGE_DIRECTORY") + TMP_CALIBRATION_FRAME_LOCATION + file_name

            # Standard captures
            cameraAction = [
                '--filename', remote_file_formatted_name,
                '--capture-image-and-download'
            ]

            #  Manual BULB Calptures
            if config.get('shutterspeed', None) == 'bulb':
                cameraAction = [
                    '--filename', remote_file_formatted_name,
                    # Open shutter
                    '--set-config', 'eosremoterelease=5',
                    # value in seconds
                    '--wait-event=' + config['exposure'],
                    # Close shutter
                    '--set-config', 'eosremoterelease=11',
                    '--capture-image-and-download',
                    # Give time for creation and download
                    '--wait-event-and-download=7s'
                ]
                del config['exposure']

            # Trigger actual camera capture
            cap_proc = await trio.run_process([
                'sh',
                current_app.config['SCRIPTS_PATH'] + '/gphoto2.sh',
                *list(itertools.chain(*[['--set-config', k + '=' +
                    '"' + v + '"'] for k, v in config.items()])),
                *cameraAction
            ], capture_stdout=True, capture_stderr=True)

            print('[CAMERA CAPTURE]')
            print(remote_file_formatted_name)

            if (cap_proc.stderr):
                print('[CAMERA CAPTURE ERROR] gphoto2.sh')
                print(cap_proc.stderr)

            capturedFilename = TMP_CALIBRATION_FRAME_LOCATION + file
            #  if 'RAW' in imageFormat else None
            raw_file = capturedFilename + '.cr2'
            jpeg_file = capturedFilename + '.jpg'

            return {
                "captures": {
                    "raw": raw_file,
                    "jpg": jpeg_file
                }
            }


        except AssertionError:
            self._log.error('Camera does not have capture capabilities')

    def preview(self):
        try:
            assert self.canCapture
            self._log.info('Capturing Preview')
        except AssertionError:
            self._log.error('Camera does not have capture capabilities')
        self._log.error('Not implemented yet')

    def record(self):
        try:
            assert self.canCapture
            self._log.info('Capturing Movie')
        except AssertionError:
            self._log.error('Camera does not have capture capabilities')
        self._log.error('Not implemented yet')

@blueprint.route('/capture', methods=['POST'])
async def capture():
    try:
        TMP_CALIBRATION_FRAME_LOCATION = f"{
            current_app.config['TMP_CALIBRATION_FRAME_LOCATION']}"
        capture_res = await capturePhoto({}, TMP_CALIBRATION_FRAME_LOCATION)
        return await make_response(capture_res.get('captures', {}), 200)

    except Exception as e:
        return await make_response(jsonify({"failed": True}), 400)


@blueprint.route('/settings/<setting>/<value>', methods=['POST'])
async def change_camera_setting(setting, value):
    try:
        cmd = f'gphoto2 --set-config-index {setting}="{value}"'
        await trio.run_process(cmd, shell=True, capture_stdout=True, capture_stderr=True)
        return await make_response(jsonify({"success": True}), 200)
    except Exception as e:
        return await make_response(jsonify({"success": False}), 400)
