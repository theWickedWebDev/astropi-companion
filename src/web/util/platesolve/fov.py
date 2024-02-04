import subprocess
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import angular_separation
from astropy.wcs import WCS

def getFOVFromExif(src):
    FOVScaleRes = subprocess.run(['exiftool','-s3','-FOV', src], capture_output=True)
    if FOVScaleRes.stdout.decode():
        FOV = float(FOVScaleRes.stdout.decode().replace(' deg', '')) 

def getFOVFromWcs(solved_wcs_fits_file, full_image_path):
    f = fits.open(solved_wcs_fits_file)
    w = WCS(f[0].header)
    origin = w.pixel_to_world(0, 0)
    IMAGEW=f[0].header['IMAGEW']
    IMAGEH=f[0].header['IMAGEH']
    hloc = w.pixel_to_world(IMAGEW, 0)
    vloc = w.pixel_to_world(0, IMAGEH)
    hfov = angular_separation(origin.ra, origin.dec, hloc.ra, hloc.dec).to("deg")
    vfov = angular_separation(origin.ra, origin.dec, vloc.ra, vloc.dec).to("deg")
    return hfov, vfov

# def getFOVFromWcs(solved_wcs_fits_file, full_image_path):
#     f = fits.open(solved_wcs_fits_file)
#     w = WCS(f[0].header)
#     IMAGEW=f[0].header['IMAGEW']
#     IMAGEH=f[0].header['IMAGEH']
#     print('IMAGEW', IMAGEW)
#     print('IMAGEH', IMAGEH)
#     horigin = w.pixel_to_world(0, IMAGEH)
#     hloc = w.pixel_to_world(IMAGEW, IMAGEH)
#     hfov = angular_separation(horigin.ra, horigin.dec, hloc.ra, hloc.dec).to("deg")

#     vorigin = w.pixel_to_world(IMAGEW, 0)
#     vloc = w.pixel_to_world(IMAGEW, IMAGEH)
#     vfov = angular_separation(vorigin.ra, vorigin.dec, vloc.ra, vloc.dec).to("deg")