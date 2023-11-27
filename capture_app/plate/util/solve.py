from quart_trio import QuartTrio
from quart import request, current_app
import subprocess
import os
import math
import json
from astropy.io import fits
from astropy import units as u
from regions import RectangleSkyRegion, PixCoord
import numpy
from astropy.coordinates import SkyCoord, angular_separation
from astropy.wcs import WCS
from capture_app._response import returnResponse
from capture_app.util.arc_second_pp import arcSecondsPerPixel 
from capture_app.util.ngc import ngc_list
from capture_app.util.get_catalog import getCoordsFromCatalog, getCatalogList, getCatalog
import traceback

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

#  scale: 'focalmm' | 'FOV' | 'ASPP' | 'safe' | 'guess'
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

def extractDataFromNewFits(fits_file):
    if (os.path.isfile(fits_file)):
        headerList=fits.open(fits_file)
        RA=headerList[0].header['CRVAL1']
        DEC=headerList[0].header['CRVAL2']
        X_PIX=headerList[0].header['CRPIX1']
        Y_PIX=headerList[0].header['CRPIX2']
        IMAGEW=headerList[0].header['IMAGEW']
        IMAGEH=headerList[0].header['IMAGEH']
    
        return {
            "ra": RA,
            "dec": DEC,
            "xCenterPixel": X_PIX,
            "yCenterPixel": Y_PIX,
            "pixelHeight": IMAGEH,
            "pixelWidth": IMAGEW
        }

def debugFitsOpen(hdulist):
    print('DEBUG')
    hdulist.info()
    print(hdulist[1].columns)
    print(hdulist[1].data)
    for r in hdulist[1].data:
        print(r)
    print('END DEBUG')

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

# def getObjectNames(solved_wcs_fits_file, full_image_path):
#     im = Image.open(full_image_path)
#     width, height = im.size
#     max = getCoordsOfPixel(solved_wcs_fits_file, width, height)
#     min = getCoordsOfPixel(solved_wcs_fits_file, 0, 0)
#     sr = RectangleSkyRegion()


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
    
def solveField(image_url=None, returnWithData=True, returnWithPoints=True, noplots=False):
        image_path = current_app.config['BASE_IMAGE_DIRECTORY'] + os.path.dirname(image_url)
        image_name= os.path.splitext(os.path.basename(image_url))[0]
        image_ext= os.path.splitext(os.path.basename(image_url))[1]

        full_image_path= image_path + image_name + image_ext
        full_solve_path= image_path + 'solves/' + image_name

        plate_solve_cmd = buildSolveCommand(src=full_image_path, dest=full_solve_path, scale="safe", noplots=noplots)

        print(' '.join(plate_solve_cmd))

        subprocess.run(plate_solve_cmd)

        solved_fits_file = full_solve_path + '/' + image_name + ".solved"
        solved_xyls_file = full_solve_path + '/' + image_name + "-indx.xyls"
        solved_wcs_fits_file = full_solve_path + '/' + image_name + ".wcs"

        return_object = {
            "success": os.path.isfile(solved_fits_file),
            "fits_files": os.listdir(full_solve_path),
            "data": {},
            "points": []
        }

        if os.path.isfile(solved_fits_file):
            new_fits_file = full_solve_path + '/' + image_name + ".new"
            if os.path.isfile(new_fits_file) and returnWithData:
                #  Handle returnWithData from ".new" data
                newExtractionData = extractDataFromNewFits(new_fits_file)
                return_object['data'] = newExtractionData

            if returnWithPoints:
                points = getXYFromFits(solved_xyls_file)
                return_object['points'] = points
                
                # getObjectNames(solved_wcs_fits_file, full_image_path)

            orientation = getOrientation(new_fits_file)
            if orientation:
                return_object['data']['orientation'] = orientation
        

        try:        
            h, v = getFOVFromWcs(solved_wcs_fits_file, full_image_path)
            center = SkyCoord(ra=return_object['data']['ra']*u.degree, dec=return_object['data']['dec']*u.degree, frame='icrs')
            f = fits.open(solved_wcs_fits_file)
            w = WCS(f[0].header)

            IMAGEW=f[0].header['IMAGEW']
            IMAGEH=f[0].header['IMAGEH']
            w.pixel_shape = IMAGEW, IMAGEH
            coords = getCoordsFromCatalog()
            pxregion=RectangleSkyRegion(center, h, v).to_pixel(w)
            pxcatalog = PixCoord.from_sky(coords, w, mode='wcs')
            indexes = numpy.argwhere(pxregion.contains(pxcatalog))
            catalogList=getCatalogList()
            catalog=getCatalog()
            
            matches={}
            for i, *_ in indexes:
                designation=str(catalogList[i][0])+str(catalogList[i][1])
                info=catalog[str(catalogList[i][0])+str(catalogList[i][1])]
                if 'obj' in info.keys():
                    matches[designation] = info['obj']
                else:
                    matches[designation] = "Star: " + info['desc']
                    
            print(matches)
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
        #         "path": full_solve_path,
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