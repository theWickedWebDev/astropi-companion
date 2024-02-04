# https://cdsarc.cds.unistra.fr/ftp/cats/VII/118/ReadMe
import numpy
from astropy.coordinates import SkyCoord
from quart import current_app
import ast
import os


def getCatalog():
    res = {}
    CATALOG_FILE = f"{current_app.config.get(
        'BIN_DIRECTORY')}/refined-catalog.dat"

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
    NGC_DAT_FILE = f"{current_app.config.get('BIN_DIRECTORY')}/ngc2000.dat"

    return numpy.genfromtxt(
        NGC_DAT_FILE,
        dtype=None,
        delimiter=[1, 5, 3, 4, 4, 3, 3, 3, 3, 3, 1, 7, 4, 1, 52],
        autostrip=True,
        encoding='utf-8'
    )


def getCoordsFromCatalog() -> SkyCoord:
    ra_list = []
    dec_list = []
    for v in getCatalog().values():
        ra_list.append(str(v['ra']))
        dec_list.append(str(v['dec']))

    _catalog = SkyCoord(ra=ra_list, dec=dec_list, frame='icrs')
    return _catalog
