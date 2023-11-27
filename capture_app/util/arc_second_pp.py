from quart import current_app

# Pixel Size / Telescope Focal Length ) X 206.265.
def arcSecondsPerPixel(fl, range_factor=.1):
        pixel_size = current_app.config['CAMERA_PIXEL_SIZE']
        arc_second_const = current_app.config['ARC_SECOND_CONSTANT']
        
        return {
            "high": (pixel_size / (fl*(1 + range_factor))) * arc_second_const,
            "low": (pixel_size / (fl*(1 - range_factor))) * arc_second_const,
            "middle": (pixel_size / fl) * arc_second_const
        }
