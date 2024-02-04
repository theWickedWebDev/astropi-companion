import trio
from quart import current_app
from regions import RectangleSkyRegion, PixCoord
import subprocess
import os
import numpy
# import traceback
# traceback.print_exc()
import math
import logging
log = logging.getLogger(__name__)

from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from ...util.get_catalog import getCatalog, getCatalogList, getCoordsFromCatalog
from ...util.arc_second_pp import arcSecondsPerPixel
from .fov import getFOVFromExif, getFOVFromWcs
from .fits import getOrientation, getXYFromFits, extractDataFromNewFits

SOLVE_DIR = 'solves/'


def buildSolveCommand(src, dest, scale=None, ra=None, dec=None, radius=None, cpulimit=30, downsample=2, noplots=False, skipsolved=False):
    focal_length_35eq = None
    FOV = None
    aspp = None
    focal_length = None
    focal_scale = None

    log.info(f'Using Solve Scale: {scale}')

    plate_solve_cmd = ['solve-field', "--crpix-center", "--overwrite", "-D", dest]

    if (skipsolved):
        plate_solve_cmd.append("--skip-solved")

    if scale == 'focalmm':
        # Get 35mm Equiv. Focal Length from Exif Data
        focalMMScaleRes = subprocess.run(
            ['exiftool', '-s3', '-FocalLength35efl', src], capture_output=True)
        if focalMMScaleRes.stdout.decode():
            focal_length_35eq = float(focalMMScaleRes.stdout.decode().split(':')[
                                      1].lstrip().split(' ')[0])
            focal_scale = ["--scale-units", "focalmm", "--scale-low", str(
                focal_length_35eq * 0.8), "--scale-high", str(focal_length_35eq * 1.2)]
            plate_solve_cmd = plate_solve_cmd + focal_scale

    # Get FOV from Exif Data
    if scale == 'FOV':
        FOV = getFOVFromExif(src)
        focal_scale = ["--scale-units", "degwidth", "--scale-low",
                       str(FOV*.8), "--scale-high", str(FOV*1.2)]
        plate_solve_cmd = plate_solve_cmd + focal_scale

    # Get Arcseconds per Pixel from Exif Data
    if scale == 'ASPP':
        p = subprocess.run(
            ['exiftool', '-s3', '-FocalLength', src], capture_output=True)
        if p.stdout.decode():
            focal_length = float(p.stdout.decode().replace(' mm', ''))
            aspp = arcSecondsPerPixel(focal_length, .1)
            focal_scale = ["--scale-units", "degwidth", "--scale-low",
                           str(aspp.get('low')), "--scale-high", str(aspp.get('high'))]
            plate_solve_cmd = plate_solve_cmd + focal_scale
    # Safe "guess" values (used on nova.astrometry.net)
    if scale == 'safe':
        focal_scale = ["--scale-units", "degwidth",
                       "--scale-low", "4", "--scale-high", "60.0"]
        plate_solve_cmd = plate_solve_cmd + focal_scale

    # Blind Solve
    if scale == 'guess' or scale == None:
        focal_scale = ["--guess-scale"]
        plate_solve_cmd = plate_solve_cmd + focal_scale

    # Limit CPU Time (seconds)
    if cpulimit != None:
        plate_cpu_limit = ["--cpulimit", str(cpulimit)]
        plate_solve_cmd = plate_solve_cmd + plate_cpu_limit

    # Generate pngs of plots
    if noplots:
        plate_solve_cmd = plate_solve_cmd + ['--no-plots']

    if downsample:
        plate_downsample = ['--downsample', str(downsample)]
        plate_solve_cmd = plate_solve_cmd + plate_downsample

    if ra and dec and radius:
        plate_ra_dec_center = [
            '--ra', str(ra), '--dec', str(dec), '--radius', str(radius)]
        plate_solve_cmd = plate_solve_cmd + plate_ra_dec_center
    elif ra and dec:
        plate_ra_dec_center = ['--ra', str(ra), '--dec', str(dec)]
        plate_solve_cmd = plate_solve_cmd + plate_ra_dec_center

    plate_solve_cmd = plate_solve_cmd + [src]

    log.debug("[PLATE SOLVE COMMAND]")
    log.debug(' '.join(plate_solve_cmd))
    return plate_solve_cmd


def logFits(file):
    f = fits.open(file)
    w = WCS(f[0].header)
    log.debug('[LOGGED FITS]')
    log.debug(file)
    log.debug(repr(f[0].header))


async def solveField(
    image_url=None,
    returnWithData=True,
    returnWithPoints=True,
    orientation=True,
    ngc=True,
    skipsolved=False,
    noplots=False
):
    log.info('PLATE SOLVING')
    image_path = os.path.dirname(image_url)
    image_name = os.path.splitext(os.path.basename(image_url))[0]
    image_ext = os.path.splitext(os.path.basename(image_url))[1]

    full_image_path = image_url
    full_solve_dir = image_path + '/' + SOLVE_DIR + image_name
    new_fits_file = full_solve_dir + '/' + image_name + ".new"
    solved_fits_file = full_solve_dir + '/' + image_name + ".solved"
    solved_xyls_file = full_solve_dir + '/' + image_name + "-indx.xyls"
    solved_wcs_fits_file = full_solve_dir + '/' + image_name + ".wcs"
    # solved_axy_fits_file = full_solve_dir + '/' + image_name + ".axy"
    # solved_corr_fits_file = full_solve_dir + '/' + image_name + ".corr"
    # solved_rdls_fits_file = full_solve_dir + '/' + image_name + ".rdls"
    # solved_match_fits_file = full_solve_dir + '/' + image_name + ".match"

    solve_img_src = full_image_path

    plate_solve_cmd = buildSolveCommand(
        src=solve_img_src,
        dest=full_solve_dir,
        scale="safe",
        noplots=noplots,
        skipsolved=skipsolved
    )

    try:
        await trio.run_process(plate_solve_cmd, capture_stdout=subprocess.DEVNULL, capture_stderr=True)

    except Exception as e:
        log.error('[PLATE SOLVE ERROR]')
        log.error(e)
        exit()

    # Creation of file signifies a solve was successful
    solve_successful = os.path.isfile(solved_fits_file)

    if not solve_successful:
        raise Exception({"error": "Plate solving failed"})

    solved_wcs_plotted_png = f'{os.path.dirname(solved_wcs_fits_file)}/{os.path.splitext(os.path.basename(
        solved_wcs_fits_file))[0]}-plot.png'
    #

    plot_cmd = [
        'plot-constellations',
        '-w',
        solved_wcs_fits_file,
        '-C',
        '-N',
        '-B',
        '-f',
        '48',
        '-j',
        '-o',
        solved_wcs_plotted_png
    ]

    await trio.run_process(plot_cmd, capture_stdout=True, capture_stderr=True)

    composite_image_src = f"{os.path.splitext(solve_img_src)[0]}-composite.jpg"
    composite_cmd = ["convert", "-composite",
                     solve_img_src, solved_wcs_plotted_png, composite_image_src]
    await trio.run_process(composite_cmd, capture_stdout=True, capture_stderr=True)

    BASE_IMAGE_DIRECTORY = current_app.config.get('BASE_IMAGE_DIRECTORY')

    return_object = {
        "success": solve_successful,
        "solved_image": solve_img_src.removeprefix(BASE_IMAGE_DIRECTORY),
        "plot_layer_image": solved_wcs_plotted_png.removeprefix(BASE_IMAGE_DIRECTORY),
        "annotated_image": composite_image_src.removeprefix(BASE_IMAGE_DIRECTORY),
        "generated_files": [f'{os.path.dirname(full_solve_dir).removeprefix('/home/pi/astropi-companion/data/captures')}/{image_name}/{d}' for d in os.listdir(full_solve_dir)],
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
            catalog = getCatalog()
            catalogList = getCatalogList()
            h, v = getFOVFromWcs(solved_wcs_fits_file, full_image_path)
            f = fits.open(solved_wcs_fits_file)
            w = WCS(f[0].header)

            center = return_object.get('data', {}).get('center')

            coords = getCoordsFromCatalog()
            pxregion = RectangleSkyRegion(center, h, v).to_pixel(w)
            pxcatalog = PixCoord.from_sky(coords, w, mode='wcs')
            indexes = numpy.argwhere(pxregion.contains(pxcatalog))
            bounds = [
                SkyCoord(SkyCoord.from_pixel(0, 0, w, origin=0, mode='all').ra, SkyCoord.from_pixel(0, 0, w, origin=0, mode='all').dec),
                SkyCoord(SkyCoord.from_pixel(pxregion.width, 0, w, origin=0, mode='all').ra, SkyCoord.from_pixel(pxregion.width, 0, w, origin=0, mode='all').dec),
                SkyCoord(SkyCoord.from_pixel(pxregion.width, pxregion.height, w, origin=0, mode='all').ra, SkyCoord.from_pixel(pxregion.width, pxregion.height, w, origin=0, mode='all').dec),
                SkyCoord(SkyCoord.from_pixel(0, pxregion.height, w, origin=0, mode='all').ra, SkyCoord.from_pixel(0, pxregion.height, w, origin=0, mode='all').dec)
            ]
            top_left_corner = SkyCoord.from_pixel(
                0, 0, w, origin=0, mode='all')
            bottom_right_corner = SkyCoord.from_pixel(
                pxregion.width, pxregion.height, w, origin=0, mode='all')
            a = pxregion.width - 0
            b = pxregion.height - 0
            pix_dist = math.sqrt(a**2 + b**2)
            separation = top_left_corner.separation(bottom_right_corner)
            # arc_seconds_total = separation.to('arcsec')
            arc_seconds_pp = separation.arcsecond / pix_dist
            return_object['data']['arcseconds_per_pixel'] = arc_seconds_pp
            return_object['data']['bounds'] = bounds

            matches = {}
            for i, *_ in indexes:
                designation = str(catalogList[i][0])+str(catalogList[i][1])
                info = catalog[str(catalogList[i][0])+str(catalogList[i][1])]

                matches[designation] = info
            return_object['objects'] = matches
        except Exception as e:
            log.error('[PLATE SOLVE ERROR]')
            log.error(e)

    return return_object
