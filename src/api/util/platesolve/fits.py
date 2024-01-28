import os
from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u
from astropy.coordinates import SkyCoord

import math

def getCoordsOfPixel(wcs_fits_file, x, y):
    try:
        if (os.path.isfile(wcs_fits_file)):
            f = fits.open(wcs_fits_file)
            w = WCS(f[0].header)
            sky = w.pixel_to_world(x,y)
            coords = sky.to_string('hmsdms').split()
            RA_HMS=coords[0]
            DEC_DMS=coords[1]
            return { "ra": RA_HMS, "dec": DEC_DMS, "x": x, "y": y }
    except:
        return
    
def extractDataFromNewFits(fits_file):
    if (os.path.isfile(fits_file)):
        headerList=fits.open(fits_file)
        RA=headerList[0].header['CRVAL1']
        DEC=headerList[0].header['CRVAL2']
        X_PIX=headerList[0].header['CRPIX1']
        Y_PIX=headerList[0].header['CRPIX2']
        IMAGEW=headerList[0].header['IMAGEW']
        IMAGEH=headerList[0].header['IMAGEH']
        ra_hma, dec_dms = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree).to_string('hmsdms').split(' ')

        return {
            "image_height": IMAGEH,
            "image_width": IMAGEW,
            "center": {
                "degrees": {
                    "ra": RA,
                    "dec": DEC
                },
                "hmsdms": {
                    "ra": ra_hma,
                    "dec": dec_dms.replace('+', '')
                },
                "pixels": {
                    "x": X_PIX,
                    "y": Y_PIX
                }
            }
        }

def getXYFromFits(fits_file):
    hdu_list = fits.open(fits_file, memmap=True)
    # debugFitsOpen(hdu_list)
    return hdu_list[1].data.tolist()

def getOrientation(fits_file):
    if (os.path.isfile(fits_file)):
        headerList=fits.open(fits_file)
        cd1_1=headerList[0].header['CD1_1']
        cd1_2=headerList[0].header['CD1_2']
        cd2_1=headerList[0].header['CD2_1']
        cd2_2=headerList[0].header['CD2_2']
        det = cd1_1 * cd2_2 - cd1_2 * cd2_1
        parity = 1.0 if det >= 0 else -1.0
        T = parity * cd1_1 + cd2_2
        A = parity * cd2_1 - cd1_2
        orientation = -math.atan2(A, T) / math.pi * 180

        return {
            "south": orientation,
            "north": 180 - orientation
        }

def debugFitsOpen(hdulist):
    print('DEBUG')
    hdulist.info()
    print(hdulist[1].columns)
    print(hdulist[1].data)
    for r in hdulist[1].data:
        print(r)
    print('END DEBUG')
