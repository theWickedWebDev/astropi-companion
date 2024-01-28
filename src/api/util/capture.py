import trio
from quart import current_app
from datetime import datetime
import itertools
from src.api.util import generateCameraConfigDict, logMessage, logError
import json

DEFAULT_FILENAME=datetime.now().strftime("%d-%m-%Y_%H:%M:%S:%f")

async def setCameraSettings(config: dict):
    if config['exposure']:
        del config['exposure']

    cmd = [
        'sh',
        current_app.config['SCRIPTS_PATH'] + '/gphoto2.sh',
        *list(itertools.chain(*[['--set-config', k + '=' + '"' + v + '"'] for k,v in config.items()]))
    ]

    cap_proc = await trio.run_process(cmd, capture_stdout=True, capture_stderr=True)   

    logMessage('[CAMERA SETTINGS UPDATED]', config)
    if (cap_proc.stderr):
        print(cap_proc.stderr.decode())
        logError('gphoto2.sh', cap_proc.stderr)

async def capturePhoto(config: dict, frame_dir=None):

    imageFormat = config.get('imageformat')

    file=DEFAULT_FILENAME # without extension
    file_name=file + '.%C' # extention

    remote_file_formatted_name=current_app.config.get("REMOTE_CAPTURE_DIRECTORY") + "/" + frame_dir + file_name

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
        *list(itertools.chain(*[['--set-config', k + '=' + '"' + v + '"'] for k,v in config.items()])),
        *cameraAction
    ], capture_stdout=True, capture_stderr=True)    
    logMessage('[CAMERA CAPTURE]', remote_file_formatted_name)
    if (cap_proc.stderr):
        logError('gphoto2.sh', cap_proc.stderr)

    # Sync remote capture directory to here
    sync_proc = await trio.run_process([
        'sh',
        current_app.config['SCRIPTS_PATH'] + '/sync.sh',
        current_app.config["REMOTE_CAPTURE_DIRECTORY"],
        current_app.config['BASE_IMAGE_DIRECTORY'],
        f"{current_app.config['REMOTE_CAPTURE_DIRECTORY']}/{frame_dir.split('/')[0]}"
    ], capture_stdout=True, capture_stderr=True)    
    logMessage('[REMOTE CAPTURE SYNCED]', remote_file_formatted_name)
    if (sync_proc.stderr):
        logError('sync.sh', sync_proc.stderr)
    
    capturedFilename = current_app.config['BASE_IMAGE_DIRECTORY'] + frame_dir + file
    raw_file = (capturedFilename + '.cr2') if 'RAW' in imageFormat else None
    jpeg_file = (capturedFilename + '.jpg') if 'JPEG' in imageFormat else None

    return {
        "captures": {
            "raw": raw_file,
            "jpg": jpeg_file
        }
    }