# https://cdsarc.cds.unistra.fr/ftp/cats/VII/118/ReadMe
# https://spider.seds.org/ngc/des.html
# 
# 
# 
# 
# 
# THIS IS A TEMPORARY ONE TIME THING
# 
# 
# 
# 
# 
from numpy import *
import numpy 
from astropy.io import fits
import re

def mapObjectTypeToName(t):
    type = t.strip()
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
    return type_name

def mapObjectDescToName(d):
    description_map = {
        "Ab": "about", 
        "n": "north",
        "n;": "north",
        "alm": "almost",
        "neb": "nebula",
        "neb*": "nebula star",
        "am": "among",
        "nf": "north following",
        "nf;": "north following",
        "app": "appended",
        "np": "north preceding",
        "np;": "north preceding",
        "att": "attached",
        "nr": "near",
        "b": "brighter",
        "N": "Nucleus",
        "N;": "Nucleus",
        "be": "between",
        "pB": "pretty bright",
        "pF": "pretty faint",
        "pF*": "pretty faint star",
        "pL": "pretty large",
        "pS": "pretty small",
        "biN": "binuclear",
        "biN?": "binuclear?",
        "p": "preceding",
        "p;": "preceding",
        "bn": "brightest towards",
        "pg": "pretty gradually the north side",
        "pm": "pretty much",
        "bs": "brightest towards the south side",
        "ps": "pretty suddenly",
        "P": "poor",
        "bp": "brightest towards the preceding side",
        "quad": "quadrilateral",
        "quar": "quartile",
        "bf": "brightest towards the following side",
        "r": "resolvable (mottled,not resolved)",
        "r?": "resolvable?",
        "B": "bright",
        "rr": "partially relolved, some stars seen",
        "rr;": "partially relolved, some stars seen",
        "c": "considerably",
        "ch": "chevelure",
        "rrr": "well resolved, clearly consisting of stars",
        "rrr;": "well resolved, clearly consisting of stars",
        "co": "coarse, coarsely",
        "com": "cometic",
        "R": "round",
        "R;": "round",
        "cont": "in contact",
        "RR": "exactly round",
        "pC": "pretty compressed",
        "pCM": "pretty compressed middle",
        "C": "compressed",
        "lC": "little compressed",
        "pRi": "pretty rich",
        "Ri": "rich",
        "C.G.H": "Cape of Good Hope",
        "s": "suddenly",
        "s;": "suddenly",
        "Cl": "cluster",
        "Cl;": "cluster",
        "Cl?": "Cluster?",
        "Cl?;": "Cluster?",
        "Cl?);": "Cluster?",
        "s": "south",
        "d": "diameter",
        "sp": "south preceding",
        "sp;": "south preceding",
        "def": "defined",
        "sf": "south following",
        "dif": "diffused",
        "dif;": "diffused",
        "cRi": "considerably rich",
        "sc": "scattered",
        "diffic": "difficult",
        "diffic;": "difficult",
        "st": "stars",
        "st;": "stars",
        "st?;": "stars?",
        "dist": "distance or distant",
        "sev": "several",
        "susp": "suspected",
        "D": "double",
        "sh": "shaped",
        "e": "extremely, excessively",
        "stell": "stellar",
        "stell;": "stellar",
        "S": "small",
        "S;": "small",
        "eRi": "extremely rich",
        "eP": "extremely poor",
        "ee": "most extremely",
        "eeL": "most extremely large",
        "sm": "smaller",
        "er": "easily resolvable",
        "triN": "trinuclear",
        "exc": "excentric",
        "trap": "trapezium",
        "E": "extended",
        "eeeF": "most extremely excessively faint",
        "v": "very",
        "vC": "very compresses",
        "vS": "very small",
        "vS;": "very small",
        "f": "following",
        "f;": "following",
        "vv": "very, very", 
        "F": "faint",
        "var": "variable",
        "eiF": "extremely irregular figure",
        "g": "gradually",
        "*": "star",
        "gr": "group",
        "i": "irregular",
        "**": "double star",
        "inv": "involved(ed|ing)",
        "inv;": "involv(ed|ing)",
        "***": "triple star",
        "iF": "irregular figure",
        "iF;": "irregular figure",
        "!": "remarkable",
        "l": "little,long",  
        "!!": "very remarkable",
        "L": "large",
        "!!!": "a magnificent or otherwise interesting object",
        "m": "much",
        "mm": "mixed magnitudes",
        "mn": "milky nebulosity",
        "st 9...": "stars from the 9th magnitude downwards",
        "M": "middle, or in the middle",
        "st 9...13": "stars from the 9th to 13th magnitude",
        # 
        "eeS": "most extremely small",
        "ns": "north suddenly",
        "ss": "south suddenly",
        "gbM": "gradually brighter middle",
        "gbM;": "gradually brighter middle",
        "cF": "considerably faint",
        "gbMN": "gradually brighter middle of Nucleus",
        "D*": "double star",
        "not": "not",
        "only": "only",
        "vnr": "very near",
        "eF": "extremely faint",
        "eF;": "extremely faint",
        "eF*": "extremely faint star",
        "sbM": "suddenly brighter middle",
        "stellar": "stellar",
        "bMSN": "brighter middle, small Nucleus",
        "lbM": "little brighter middle",
        "lbM;": "little brighter middle",
        "vF": "very faint",
        "vF;": "very faint",
        "eL": "extremely large",
        "mE": "much extended",
        "cC": "considerably compressed",
        "vRi": "very rich",
        "vmC": "very much compressed",
        "eS": "extremely small",
        "eS;": "extremely small",
        "*?": "star?",
        "eeF": "most extremely faint",
        "bet": "between",
        "vP": "very poor",
        "iR": "irregular round",
        "cS": "considerably small",
        "cL": "considerably large",
        "cB": "considerably bright",
        "mbM": "much brighter middle",
        "vgmbM": "very gradually much brighter middle",
        "gmbM": "gradually much brighter middle",
        "vglbM": "very gradually a little brighter middle",
        "glbM": "gradually a little brighter middle",
        "glbM;": "gradually a little brighter middle",
        "vgbM": "very gradually brighter middle",
        "gpmbM": "gradually pretty much brighter middle",
        "cbM": "considerably brighter middle",
        "pgbM": "pretty gradually brighter middle",
        "smbM": "suddenly much brighter middle",
        "bMN": "brighter middle nucleus",
        "vlbM": "very little brighter middle",
        "vgvlbM": "very gradual very little brighter middle",
        "gvlbM": "gradual very little brighter middle",
        "vsmbM": "very suddenly much brighter middle",
        "slbM": "suddenly less brighter middle",
        "vsbM": "very suddenly brighter middle",
        "sbMN": "suddenly brighter middle of the Nucleus",
        "lbMN": "less bright middle of the Nucleus",
        "glbMN": "gradually less bright middle of the Nucleus",
        "smbMN": "suddenly much brighter middle of the nucleus",
        "pgmbM": "pretty gradual much brighter middle",
        "vgpmbM": "very gradual pretty much brighter middle",
        "vmbMBN": "very much bright middle bright nucleus",
        "bM": "brighter middle",
        "bM;": "brighter middle",
        "vL": "very large",
        "pf": "pretty faint",
        "pB*": "pretty bright star",
        "vS*": "very small star",
        "vS**": "very small double star",
        "vF*": "very faint star",
        "D?": "Double?",
        "bM*": "bright middle star",
        "(D*": "(Double star",
        "M?)": "middle?)",
        "vSN": "very small nucleus",
        "mCM": "much compressed middle",
        "bMN": "bright middle of the Nucleus",
        "vB": "Very bright",
        "vLE": "very large extended",
        "pmC": "pretty much compressed",
        "vmbM": "very much brighter middle",
        "pgvmbM": "pretty gradual very much brighter middle",
        "PN": "Poor nucleus",
        "Cl?)": "cluster?)",
        "eS*": "extremely small star",
        "cl": "considerably little",
        "cl.": "considerably little",
        "vlC": "very little compressed",
        "vg": "very gradually",
        "cE": "considerably extended",
        "PN": "poor nucleus",
        "vvlE": "extended very very little",
        "decl": "diameter exceedingly considerably large"
    }

    desc = d.strip()
    return description_map[desc]

objects = []
names_list = {}

# ------------------------------
# Create dictionary of names
# ------------------------------
for x in numpy.genfromtxt(
        "/home/telescope/companion/api/util/dat/names.dat",
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
        names_list[key] = {"obj": obj, "des": des, "name": name, "comment": comment }
        # if key in objects.keys():
        #     objects[key]['obj'] = obj
        #     objects[key]['desc'] = objects[key]['desc'] + " " + comment

# ------------------------------
# Replaces "type" with human readable versions
# ------------------------------
with fits.open('/home/telescope/companion/api/util/dat/VII_118.fits') as hdul:
    objectList = hdul[1].data
    cols = hdul[1].columns
    for b in objectList:
        rewritten={}
        for col in cols.names:
            rewritten[col]=b.field(col)
        rewritten['Name'] = ''.join(b['Name'].split(' '))
        rewritten['Type'] = mapObjectTypeToName(b['type'])
        rewritten['Dec_sign'] = b['DE-']

        if rewritten['Name'] in names_list.keys():
            rewritten['Obj'] = names_list[rewritten['Name']]['obj']
            rewritten['Comment'] = names_list[rewritten['Name']]['comment']
        objects.append(rewritten)

# ------------------------------
# DESCRIPTION FIND AND REPLACE'S
# ------------------------------

# Regex Patterns
star_mag_pattern = r"[\*][\d]+"
stars_of_magnitude_pattern = r"[\d]{1,2}[\.]{3}[\d]{0,2}" # 5...10 or 9...
pretty_suddenly_pattern = r"^[p][s]"
neb_pattern = r"[n][e][b]"
star_desc_pattern = r"^[a-xA-Z][\*]{1,3}"
extended_replacements = (
  ("iE", "irregularly extended"),
  ("lE", "a little extended"),
  ("vlE", "extended very little"),
  ("vvlE", "extended very very little"),
  ("mE", "much extended"),
  ("vmE", "very much extended"),
  ("pmE", "pretty much extended"),
  ("E", "extended"),
  ("eE", "extremely extended"),
  ("cE", "considerably extended"),
)

extended_replacements_pattern = re.compile(
  "|".join(re.escape(k) for k, _ in extended_replacements
))
# End Regex Patterns

for i in objects:
    desc_parts = []
    for k in i['Desc'].split(", "):
        split_parts = []
        if (' of ' in k and ' of magnitude' not in k):
            split_parts.append(k) 
        elif re.match(extended_replacements_pattern, k):
            mapping = { k: v for k, v in extended_replacements }
            result = extended_replacements_pattern.sub(lambda x: mapping[x[0]], k, count=1)
        else:
            for l in k.split(' '):
                try:
                    if l in ('a'):
                        continue
                    elif re.match(star_mag_pattern, l):
                        d = mapObjectDescToName(l[0])
                        dd = ' of magnitude ' + l[1:]
                        split_parts.append(d + dd)
                    elif re.match(stars_of_magnitude_pattern, l):
                        p = l.split('...')
                        r = 'magnitudes ' + p[0]
                        if p[1]:
                            r += ' to ' + p[1]
                        else:
                            r += ' and up'
                        split_parts.append(r)
                    elif re.match(pretty_suddenly_pattern, l):
                        answer = [mapObjectDescToName(x) for x in [*l[2:]]]
                        split_parts.append(' '.join(answer))
                    elif re.match(neb_pattern, l):
                        if (l == 'neb'):
                            split_parts.append(mapObjectDescToName(l))
                        elif (l == 'neb*'):
                            split_parts.append(mapObjectDescToName(l))
                        else:
                            split_parts.append(l)
                    elif re.match(star_desc_pattern, l):
                        d = mapObjectDescToName(l[0])
                        questionable = '?' in l
                        v = mapObjectDescToName(l[1:].replace('a ', '').replace('?', ''))
                        answer = 'a ' + d + ' ' + v
                        if questionable:
                            answer = 'maybe ' + answer
                        split_parts.append(answer)
                    else:
                        split_parts.append(mapObjectDescToName(l))
                        # 
                except Exception as e:
                    split_parts.append(l)
            desc_parts.append(', '.join(split_parts))
    final_dict = ' | '.join(desc_parts)
    i['Desc'] = final_dict

with open('/home/telescope/companion/api/util/dat/refined-catalog.dat', 'w') as f:
    for line in objects:
        f.write("%s\n" % line)

print('done!')