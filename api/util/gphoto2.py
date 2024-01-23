import trio
from quart import current_app
from api.util import CAMERA_SETTINGS_DICT_BY_NAME

async def getCurrentConfigValue(config_name):
    if (current_app.config.get('MOCK_CAMERA_ENABLED')):
        if (config_name == 'lensname'):
            return 'Mocked Canon EF-S Lens'
        if (config_name == 'aperture'):
            return 5.6
        if (CAMERA_SETTINGS_DICT_BY_NAME.get(config_name)):
            return CAMERA_SETTINGS_DICT_BY_NAME.get(config_name).get('_default', "")

    cmd = await trio.run_process([
        'sh',
        current_app.config['SCRIPTS_PATH'] + '/gphoto2.sh',
        '--get-config',
        config_name
    ], capture_stdout=True, capture_stderr=True)    
    if (cmd.stdout):
        for l in cmd.stdout.decode().split('\n'):
            if ('Current:' in l):
                return l.replace('Current: ', '')
    if (cmd.stderr):
        raise Exception(cmd.stderr)

async def setCurrentConfigValue(config_name, config_value):
    if (not current_app.config.get('MOCK_CAMERA_ENABLED')):
        cmd = await trio.run_process([
            'sh',
            current_app.config['SCRIPTS_PATH'] + '/gphoto2.sh',
            '--set-config',
            f"{config_name}={config_value}"
        ], capture_stdout=True, capture_stderr=True)    
        if (cmd.stdout):
            for l in cmd.stdout.decode().split('\n'):
                if ('Current:' in l):
                    return l.replace('Current: ', '')
        if (cmd.stderr):
            raise Exception(cmd.stderr)