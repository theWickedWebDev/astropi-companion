# Pixel Size / Telescope Focal Length ) X 206.265.
def arcSecondsPerPixel(fl, range_factor=.1):
        CAMERA_PIXEL_SIZE=4.3
        ARC_SECOND_CONSTANT=206.265
        
        return {
            "high": (CAMERA_PIXEL_SIZE / (fl*(1 + range_factor))) * ARC_SECOND_CONSTANT,
            "low": (CAMERA_PIXEL_SIZE / (fl*(1 - range_factor))) * ARC_SECOND_CONSTANT,
            "middle": (CAMERA_PIXEL_SIZE / fl) * ARC_SECOND_CONSTANT
        }
