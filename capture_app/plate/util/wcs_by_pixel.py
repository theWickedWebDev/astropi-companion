import os
import json
from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u
from astropy.coordinates import SkyCoord

def getCoordsOfPixel(wcs_fits_file, x, y):
    try:
        if (os.path.isfile(wcs_fits_file)):
            f = fits.open(wcs_fits_file)
            w = WCS(f[0].header)
            sky = w.pixel_to_world(0,0)
            coords = sky.to_string('hmsdms').split()
            RA_HMS=coords[0]
            DEC_DMS=coords[1]
            return { "ra": RA_HMS, "dec": DEC_DMS, "x": x, "y": y }
    except:
        return