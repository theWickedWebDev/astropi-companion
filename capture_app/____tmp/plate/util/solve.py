from quart import current_app
from regions import RectangleSkyRegion, PixCoord
import subprocess
import os
import numpy
import traceback

from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from capture_app.util.arc_second_pp import arcSecondsPerPixel 
from capture_app.util.get_catalog import getCoordsFromCatalog, catalog, catalogList
from .fov import getFOVFromExif, getFOVFromWcs
from .fits import getOrientation, getXYFromFits, extractDataFromNewFits 

SOLVE_DIR='solves/'

def buildSolveCommand(src, dest, scale=None, ra=None, dec=None, radius=None, cpulimit=None, downsample=2, noplots=False):
    focal_length_35eq=None
    FOV=None
    aspp=None
    focal_length=None
    focal_scale=None
    
    plate_solve_cmd=['solve-field', "--crpix-center", "-D", dest, "--overwrite"]
    
    if scale == 'focalmm':
        # Get 35mm Equiv. Focal Length from Exif Data
        focalMMScaleRes = subprocess.run(['exiftool','-s3','-FocalLength35efl',src], capture_output=True)           
        if focalMMScaleRes.stdout.decode():
            focal_length_35eq = float(focalMMScaleRes.stdout.decode().split(':')[1].lstrip().split(' ')[0])
            focal_scale = [ "--scale-units", "focalmm", "--scale-low", str(focal_length_35eq * 0.8), "--scale-high", str(focal_length_35eq * 1.2)]
            plate_solve_cmd = plate_solve_cmd + focal_scale

    # Get FOV from Exif Data
    if scale == 'FOV':
        FOV = getFOVFromExif(src)  
        focal_scale = [ "--scale-units", "degwidth", "--scale-low", str(FOV*.8), "--scale-high", str(FOV*1.2)]
        plate_solve_cmd = plate_solve_cmd + focal_scale

    # Get Arcseconds per Pixel from Exif Data
    if scale == 'ASPP':
        p = subprocess.run(['exiftool', '-s3', '-FocalLength', src ], capture_output=True)
        if p.stdout.decode():
            focal_length = float(p.stdout.decode().replace(' mm', ''))
            aspp = arcSecondsPerPixel(focal_length, .1)
            focal_scale = [ "--scale-units", "degwidth", "--scale-low", str(aspp.low), "--scale-high", str(aspp.high)]
            plate_solve_cmd = plate_solve_cmd + focal_scale

    # Safe "guess" values (used on nova.astrometry.net)
    if scale == 'safe':
        focal_scale = ["--scale-units", "degwidth", "--scale-low", "0.1", "--scale-high", "180.0"]
        plate_solve_cmd = plate_solve_cmd + focal_scale

    # Blind Solve
    if scale == 'guess' or scale == None:
        focal_scale = ["--guess-scale"]
        plate_solve_cmd = plate_solve_cmd + focal_scale

    # Limit CPU Time (seconds)
    if cpulimit != None:
        plate_cpu_limit=["--cpulimit", cpulimit]
        plate_solve_cmd = plate_solve_cmd + plate_cpu_limit
    
    # Generate pngs of plots
    if noplots:
        plate_solve_cmd = plate_solve_cmd + ['--no-plots']

    if downsample:
        plate_downsample=['--downsample', str(downsample)]
        plate_solve_cmd = plate_solve_cmd + plate_downsample

    if ra and dec and radius:
        plate_ra_dec_center=['--ra', str(ra),'--dec', str(dec), '--radius', str(radius)]
        plate_solve_cmd = plate_solve_cmd + plate_ra_dec_center
    elif ra and dec:
        plate_ra_dec_center=['--ra', str(ra),'--dec', str(dec) ]
        plate_solve_cmd = plate_solve_cmd + plate_ra_dec_center

    plate_solve_cmd = plate_solve_cmd + [src]
    return plate_solve_cmd
    
def solveField(
    image_url=None,
    returnWithData=True,
    returnWithPoints=True,
    noplots=False,
    orientation=True,
    ngc=True
):
    image_path = current_app.config['BASE_IMAGE_DIRECTORY'] + os.path.dirname(image_url)
    image_name= os.path.splitext(os.path.basename(image_url))[0]
    image_ext= os.path.splitext(os.path.basename(image_url))[1]
    full_image_path= image_path + image_name + image_ext
    full_solve_dir= image_path + SOLVE_DIR + image_name     
    new_fits_file = full_solve_dir + '/' + image_name + ".new"
    solved_fits_file = full_solve_dir + '/' + image_name + ".solved"
    solved_xyls_file = full_solve_dir + '/' + image_name + "-indx.xyls"
    solved_wcs_fits_file = full_solve_dir + '/' + image_name + ".wcs"

    plate_solve_cmd = buildSolveCommand(
        src=full_image_path, 
        dest=full_solve_dir, 
        scale="safe", 
        noplots=noplots, 
    )

    print('Running Command:')
    print(' '.join(plate_solve_cmd))
    print('')

    subprocess.run(plate_solve_cmd)

    # Creation of file signifies a solve was successful
    solve_successful = os.path.isfile(solved_fits_file)

    if not solve_successful:
        # FIXME: 
        return { "success": solve_successful }

    return_object = {
        "success": solve_successful,
        "fits_files": os.listdir(full_solve_dir),
        "data": {},
        "points": []
    }

    if os.path.isfile(new_fits_file) and returnWithData:
        newExtractionData = extractDataFromNewFits(new_fits_file)
        return_object['data'] = newExtractionData

    if returnWithPoints:
        points = getXYFromFits(solved_xyls_file)
        return_object['points'] = points

    if orientation:
        return_object['data']['orientation'] = getOrientation(new_fits_file)
    
    if ngc:
        try:        
            h, v = getFOVFromWcs(solved_wcs_fits_file, full_image_path)
            f = fits.open(solved_wcs_fits_file)
            w = WCS(f[0].header)
            center = SkyCoord(
                ra=return_object['data']['raCenter']*u.degree,
                dec=return_object['data']['decCenter']*u.degree,
                frame='icrs'
            )

            coords = getCoordsFromCatalog()
            pxregion=RectangleSkyRegion(center, h, v).to_pixel(w)
            pxcatalog = PixCoord.from_sky(coords, w, mode='wcs')
            indexes = numpy.argwhere(pxregion.contains(pxcatalog))

            matches={}
            for i, *_ in indexes:
                designation=str(catalogList[i][0])+str(catalogList[i][1])
                info=catalog[str(catalogList[i][0])+str(catalogList[i][1])]

                matches[designation] = info
                    
            return_object['objects'] = matches
        except Exception as e:
            print(e)
            traceback.print_exc()

    return return_object

    # RA_HMS=None
    # DEC_DMS=None
    # sep=None
    # X_PIX=None
    # Y_PIX=None

    # pixelCoord = getCoordsOfPixel(solved_wcs_fits_file, 2856.06380208, 2856.06380208)
    # print('pixelCoord', pixelCoord)
    
    # if (os.path.isfile(new_fits_file)):
    #     headerList=fits.open(new_fits_file)

    #     RA=headerList[0].header['CRVAL1']
    #     DEC=headerList[0].header['CRVAL2']
    #     X_PIX=headerList[0].header['CRPIX1']
    #     Y_PIX=headerList[0].header['CRPIX1']

    #     if (RA and DEC):
    #         # TODO: Somehow make these values available outside of this script (bash, python, etc..)
    #         c = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')

    #         try:
    #             # if (expectedRA and expectedDEC):
    #             #     print('Expected RA:', expectedRA)
    #             #     print('Expected DEC:', expectedDEC) 

    #             #     c2 = SkyCoord(ra=str(expectedRA), dec=str(expectedDEC), frame='icrs')
    #             #     sep = c.separation(c2)
    #             #     print("Diff:", sep)

    #             coords = c.to_string('hmsdms').split()

    #             RA_HMS=coords[0]
    #             DEC_DMS=coords[1]

    #             # calibrateUrl = 'http://10.0.0.200:8765/api/calibrate/?ra=' + RA_HMS + '&dec=' + DEC_DMS
    #             # x = requests.post(calibrateUrl)
    #             # print("")
    #             # print(x.text)
    #             # print(x.status_code == 200)
    #         except:
    #             print('todo error')
        
    # return await returnResponse({ 
    #     "config": {
    #         "image": image_url,
    #         "expectedRA": expectedRA or None,
    #         "expectedDEC": expectedDEC or None,
    #     }, 
    #     "exif": {
    #         "arcSecondsPerPixel": aspp or None,
    #         "focalLength": focal_length or None,
    #         "FOV": FOV or None
    #     },
    #     "solved": {
    #         "path": full_solve_dir,
    #         "ra": RA_HMS or None,
    #         "dec": DEC_DMS or None,
    #         "xPixel": X_PIX or None,
    #         "yPixel": X_PIX or None,
    #         "separation": sep or None,
    #     }
    # }, 200)
# except Exception as e:
#     print(e)
#     return await returnResponse({ "error": e.args[0] }, 400)