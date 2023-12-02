import trio
from time import sleep
from ..config import config
import pprint
from datetime import datetime

pp = pprint.PrettyPrinter(indent=2)

async def capture(scope: trio.CancelScope, stack_name):
    config.setStackConfig(stack_name, { 'START_TIME': datetime.now().strftime("%m-%d-%Y %H:%M:%S") })
    settings = config.getStackConfig(stack_name)
    print('>> Starting Capture')
    pp.pprint(settings)

    frames=int(settings['FRAMES'])
    with scope:
        for i in range(frames):

            res = await trio.run_process(['echo', 'capturing frame ' + str(i) + ' of ' + str(frames)],
                capture_stdout=True, capture_stderr=True
            )

            lines = res.stdout.splitlines()
            for line in lines:
                print(line.decode())
        config.setStackConfig(stack_name, { 'END_TIME': datetime.now().strftime("%m-%d-%Y %H:%M:%S") })