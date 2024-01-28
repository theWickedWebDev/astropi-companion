from enum import Enum

class TelescopeControlMethods(Enum):
    GOTO = 'goto'
    CALIBRATE = 'calibrate'

class TelescopeTargetTypes(Enum):
    RA_DEC = 'RA_DEC'
    SOLAR_SYSTEM = 'SOLAR_SYSTEM'
    BY_NAME = 'BY_NAME'

DEFAULT_LIGHT_FRAMES_COUNT = 75
DEFAULT_FLAT_FRAMES_COUNT = 75
DEFAULT_DARK_FRAMES_COUNT = 75

MOCKED_LIGHT_FRAME_JPG = '/home/telescope/companion/api/mock_photos/light-frame.jpg'
MOCKED_LIGHT_FRAME_G1_00_JPG = '/home/telescope/companion/api/mock_photos/light-frame_01_000.jpg'
MOCKED_LIGHT_FRAME_G1_01_JPG = '/home/telescope/companion/api/mock_photos/light-frame_01_001.jpg'
MOCKED_LIGHT_FRAME_G1_02_JPG = '/home/telescope/companion/api/mock_photos/light-frame_01_002.jpg'
MOCKED_LIGHT_FRAME_G1_03_JPG = '/home/telescope/companion/api/mock_photos/light-frame_01_003.jpg'
MOCKED_LIGHT_FRAME_G1_04_JPG = '/home/telescope/companion/api/mock_photos/light-frame_01_004.jpg'
MOCKED_LIGHT_FRAME_G1_05_JPG = '/home/telescope/companion/api/mock_photos/light-frame_01_005.jpg'


