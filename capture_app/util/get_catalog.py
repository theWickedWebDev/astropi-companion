# https://cdsarc.cds.unistra.fr/ftp/cats/VII/118/ReadMe
from numpy import *
import numpy
from astropy.coordinates import SkyCoord
import ast

BIN_DIRECTORY='/home/telescope/capture-app/capture_app/bin/'

def getCatalog():
    res = {}
    with open(BIN_DIRECTORY + 'refined-catalog.dat', 'r') as file:
        for line in file:
            line = line.strip()
            d = ast.literal_eval(line)

            n_mag = "Visual"
            if d['n_mag'] == "p":
                n_mag = "Photographic"

            obj = d['Name']
            if 'Obj' in d.keys():
                obj = d['Obj']

            res[d['Name']] = {
                "id": d['Name'],
                "object": obj,
                "ra": str(d['RAh']) + 'h' + str(d['RAm']) + 'm',
                "dec": str(d['DE-']) + str(d['DEd']) + 'd' + str(d['DEm']) + 'm',
                "constellation": d['Const'],
                "mag": d['mag'],
                "n_mag": n_mag,
                "description": d['Desc']
            }
    return res


def getCatalogList():
    return numpy.genfromtxt(
        BIN_DIRECTORY + 'ngc2000.dat',
        dtype=None,
        delimiter=[ 1, 5, 3, 4, 4, 3, 3, 3, 3, 3, 1, 7, 4, 1, 52 ],
        autostrip=True,
        encoding='utf-8'
    )


def getCoordsFromCatalog():
    ra_list = []
    dec_list = []
    for v in catalog.values():
        ra_list.append(str(v['ra']))
        dec_list.append(str(v['dec']))

    _catalog = SkyCoord(ra=ra_list, dec=dec_list, frame='icrs')
    return _catalog


# Should be able to only need one of these (or at least share same file)
catalog = getCatalog()
catalogList = getCatalogList()