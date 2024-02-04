import trio
from quart import current_app
from datetime import datetime
import itertools


async def setCameraSettings(config: dict):
    if config['exposure']:
        del config['exposure']

    cmd = [
        'sh',
        current_app.config['SCRIPTS_PATH'] + '/gphoto2.sh',
        *list(itertools.chain(*[['--set-config', k + '=' + '"' + v + '"'] for k, v in config.items()]))
    ]

    cap_proc = await trio.run_process(cmd, capture_stdout=True, capture_stderr=True)

    print('[CAMERA SETTINGS UPDATED]')
    print(config)
    if (cap_proc.stderr):
        print(cap_proc.stderr.decode())
        print('[ERROR] gphoto2.sh')
        print(cap_proc.stderr)


async def capturePhoto(config: dict, frame_dir=None):

    imageFormat = config.get('imageformat')

    DEFAULT_FILENAME = datetime.now().strftime("%d-%m-%Y_%H:%M:%S:%f")
    file = DEFAULT_FILENAME  # without extension
    file_name = file + '.%C'  # extention

    remote_file_formatted_name = current_app.config.get(
        "BASE_IMAGE_DIRECTORY") + frame_dir + file_name

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

    capturedFilename = frame_dir + file
    #  if 'RAW' in imageFormat else None
    raw_file = capturedFilename + '.cr2'
    jpeg_file = capturedFilename + '.jpg'

    return {
        "captures": {
            "raw": raw_file,
            "jpg": jpeg_file
        }
    }
