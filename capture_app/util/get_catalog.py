# https://cdsarc.cds.unistra.fr/ftp/cats/VII/118/ReadMe
from numpy import *
import numpy
from astropy.coordinates import SkyCoord
import ast

BIN_DIRECTORY='/home/telescope/capture-app/capture_app/bin/'
CATALOG_FILE=BIN_DIRECTORY + 'refined-catalog.dat'
NGC_DAT_FILE=BIN_DIRECTORY + 'ngc2000.dat'

def getCatalog():
    res = {}
    with open(CATALOG_FILE, 'r') as file:
        for line in file:
            d = ast.literal_eval(line.strip())
            res[d['Name']] = {
                "id": d['Name'],
                "object": d['Obj'] if 'Obj' in d.keys() else d['Name'],
                "ra": str(d['RAh']) + 'h' + str(d['RAm']) + 'm',
                "dec": str(d['DE-']) + str(d['DEd']) + 'd' + str(d['DEm']) + 'm',
                "constellation": d['Const'],
                "mag": d['mag'],
                "n_mag": "Photographic" if d['n_mag'] == "p" else "Visual",
                "description": d['Desc']
            }
    return res


def getCatalogList() -> list:
    return numpy.genfromtxt(
        NGC_DAT_FILE,
        dtype=None,
        delimiter=[ 1, 5, 3, 4, 4, 3, 3, 3, 3, 3, 1, 7, 4, 1, 52 ],
        autostrip=True,
        encoding='utf-8'
    )


def getCoordsFromCatalog() -> SkyCoord:
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