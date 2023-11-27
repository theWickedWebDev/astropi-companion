# https://cdsarc.cds.unistra.fr/ftp/cats/VII/118/ReadMe
from numpy import *
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates import ICRS, Galactic, FK4, FK5
from astropy.wcs import WCS
from astropy.io import fits

objects = []
with fits.open('/home/telescope/capture-app/capture_app/util/VII_118.fits') as hdul:
    objectList = hdul[1].data
    cols = hdul[1].columns
    print(cols.names)

    # print(type(objectList))
    for b in objectList:
        rewritten={}
        for col in cols.names:
            rewritten[col]=b.field(col)
        
        type = b['Type'].strip()
        type_name = ""
        match type:
            case 'Gx':
                type_name="Galaxy"
            case 'OC':
                type_name="Open star cluster"
            case 'Gb':
                type_name="Globular star cluster"
            case 'Nb':
                type_name="Bright emission or reflection nebula"
            case 'Pl':
                type_name="Planetary nebula"
            case 'C+N':
                type_name="Cluster associated with nebulosity"
            case 'AST':
                type_name="Asterism or group of a few stars"
            case 'Kt':
                type_name="Knot  or  nebulous  region  in  an  external galaxy"
            case '***':
                type_name="Triple star"
            case 'D*':
                type_name="Double star"
            case '*':
                type_name="Single star"
            case '?':
                type_name="Uncertain type or may not exist"
            case '':
                type_name="Unidentified at the place given"
            case '-':
                type_name="Object called nonexistent in the RNGC"
            case 'PD':
                type_name="Photographic plate defect"
            case _:
                type_name=""
        
        print('type_name:', type_name)
        rewritten['Type'] = type_name
        # print(rewritten)
        objects.append(rewritten)

print(objects[0])

# for b in f[2].data:
#     names[b[1]] = b[0]

def getCatalogList():
    return numpy.genfromtxt(
        "/home/telescope/capture-app/capture_app/util/ngc2000.dat",
        dtype=None,
        delimiter=[
            1, # designation
            5, # name
            3, # t
            4, # ra_hr
            4, # ra_min
            3, # dec_sign
            3, # dec_deg
            3, # dec_arcmin
            3, # src
            3, # const
            1, # l_size
            7, # size
            4, # mag
            1, # n_mag
            52 # desc
        ],
        autostrip=True,
        encoding='utf-8'
    )

def getCatalog():
    objects = {}
    labels = ["designation", "name", "t", "ra_hr", "ra_min", "dec_sign", "dec_deg", "dec_arcmin", "src", "const", "l_size", "size", "mag", "n_mag", "desc"]

    for x in numpy.genfromtxt(
        "/home/telescope/capture-app/capture_app/util/ngc2000.dat",
        dtype=None,
        delimiter=[
            1, # designation
            5, # name
            3, # t
            4, # ra_hr
            4, # ra_min
            3, # dec_sign
            3, # dec_deg
            3, # dec_arcmin
            3, # src
            3, # const
            1, # l_size
            7, # size
            4, # mag
            1, # n_mag
            52 # desc
        ],
        autostrip=True,
        encoding='utf-8'
    ):
        objects[f"{x[0]}{x[1]}"] = dict(zip(labels, x))

    for x in numpy.genfromtxt(
        "/home/telescope/capture-app/capture_app/util/names.dat",
        dtype=None,
        delimiter=[
            36, # obj
            1, # designation
            5, # name
            8, # comment
        ],
        autostrip=True,
        encoding='utf-8'
    ):
        obj=x[0]
        des=x[1]
        name=x[2]
        comment=x[3]
        
        key = str(des)+str(name)

        if key in objects.keys():
            objects[key]['obj'] = obj
            objects[key]['desc'] = objects[key]['desc'] + " " + comment
    
    return objects

def getCoordsFromCatalog():
    o = getCatalog()
    ra_list = []
    dec_list = []
    for v in o.values():
        item = o[str(v['designation']) + str(v['name'])]
        ra=str(item['ra_hr']) + 'h' + str(item['ra_min']) + 'm'
        dec=str(item['dec_sign']) + str(item['dec_deg']) + 'd' + str(item['dec_arcmin']) + 'm'
        ra_list.append(ra)
        dec_list.append(dec)

    catalog = SkyCoord(ra=ra_list, dec=dec_list, frame='icrs')
    return catalog

# SkyCoord("00h02m30s +03d20m00s", frame='icrs')
# idx, sep2d, dist3d = SkyCoord("00h02m30s +03d20m00s", frame='icrs').match_to_catalog_sky(getCoordsFromCatalog(), nthneighbor=1)
# print(idx, sep2d, dist3d)

# with open(r'/home/telescope/capture-app/capture_app/util/get_catalog.txt', 'w') as fp:
#     for item in getCoordsFromCatalog():
#         fp.write("%s\n" % item.to_string(style="hmsdms"))