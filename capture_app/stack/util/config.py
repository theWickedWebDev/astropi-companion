# https://cdsarc.cds.unistra.fr/ftp/cats/VII/118/ReadMe
import subprocess

BASE_IMAGE_DIRECTORY="/home/telescope/captures/"
CONFIG_FILE_NAME='config.ini'
CONFIG_KEYS=(
    "DATE",
    "TARGET_NAME",
    "TARGET_RA",
    "TARGET_DEC",
    "FRAMES",
    "ISO",
    "APERTURE",
    "EXPOSURE_SECONDS",
    "FOCAL",
    "IMAGEFORMAT",
    "AUTOEXPOSUREMODE",
    "PICTURESTYLE",
    "HISTOGRAM",
    "START_TIME",
    "END_TIME"
)

def getStackConfig(name):
    res = {}
    with open(BASE_IMAGE_DIRECTORY + name + '/' + CONFIG_FILE_NAME, 'r') as file:
        for line in file:
            line = line.strip()
            key, val = line.split('=')
            res.update({ key: val})
    
    vals = {}
    for key in res.keys():
        if key in CONFIG_KEYS:
            vals[key] = res[key]

    return vals

def setStackConfig(name, raw_vals):
    vals = {}
    error_keys = []
    for key in raw_vals.keys():
        if key in CONFIG_KEYS:
            vals[key] = raw_vals[key]
        else:
            error_keys.append("'" + key + "' is not a valid configuration property")
    res = getStackConfig(name)
    for key in vals.keys():
        res[key] = vals[key]
    subprocess.run(['rm', BASE_IMAGE_DIRECTORY + name + '/' + CONFIG_FILE_NAME, 'w'])
    with open(BASE_IMAGE_DIRECTORY + name + '/' + CONFIG_FILE_NAME, 'w') as file:
        for key in res.keys():
            item=str(key) + '=' + str(res[key])
            file.write("%s\n" % item)
    return res, error_keys