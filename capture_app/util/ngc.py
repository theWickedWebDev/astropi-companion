import numpy

def ngc_list():
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