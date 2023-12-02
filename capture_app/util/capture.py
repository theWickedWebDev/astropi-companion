import trio
from quart import current_app
from datetime import datetime
import itertools
from capture_app.util import generateCameraConfigDict

DEFAULT_FILENAME=datetime.now().strftime("%d-%m-%Y_%H:%M:%S:%f")

async def capturePhoto(conf: dict):
    config, errors = generateCameraConfigDict(conf)

    imageFormat = config['imageformat']

    file=DEFAULT_FILENAME # without extension
    file_name=file + '.%C' # extention
    remote_capture_directory=current_app.config["REMOTE_CAPTURE_DIRECTORY"]
    local_capture_directory = current_app.config['BASE_IMAGE_DIRECTORY']
    remote_file_formatted=remote_capture_directory + "/" + file_name

    raw_file = (local_capture_directory + file + '.cr2') if 'RAW' in imageFormat else None
    jpeg_file = (local_capture_directory + file + '.jpg') if 'JPEG' in imageFormat else None

    try:
        # Standard captures
        cameraAction = [
            '--filename', remote_file_formatted,
            '--capture-image-and-download'
        ]

        #  Manual BULB Calptures
        if config['shutterspeed'] == 'bulb':
            cameraAction = [
                '--filename', remote_file_formatted,
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
        if (cap_proc.stderr):
            print(cap_proc.stderr.decode())

        # Sync remote capture directory to here
        sync_proc = await trio.run_process([
            'sh',
            current_app.config['SCRIPTS_PATH'] + '/sync.sh',
            remote_capture_directory,
            local_capture_directory
        ], capture_stdout=True, capture_stderr=True)    

        if (sync_proc.stderr):
            print(sync_proc.stderr.decode())
        else:
            print('Capture synced to local')

        return {
            "captures": {
                "raw": raw_file,
                "jpg": jpeg_file
            },
            "errors": errors
        }
    
    except Exception as e:
        print('capture exception', e)
        return

