from quart import request
from capture_app._response import returnResponse
from ._blueprint import blueprint
from .util.solve import solveField

@blueprint.route("/field/", methods=["POST"])
async def solve_field():
    try:
        res = await request.json
        
        solve_response = solveField(image_url=res['image'], returnWithData=True, returnWithPoints=True, noplots=False)

        # c = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')

        # try:
        #     # if (expectedRA and expectedDEC):
        #     #     print('Expected RA:', expectedRA)
        #     #     print('Expected DEC:', expectedDEC) 

        #     #     c2 = SkyCoord(ra=str(expectedRA), dec=str(expectedDEC), frame='icrs')
        #     #     sep = c.separation(c2)
        #     #     print("Diff:", sep)

        #     coords = c.to_string('hmsdms').split()

        #     RA_HMS=coords[0]
        #     DEC_DMS=coords[1]

        #     # calibrateUrl = 'http://10.0.0.200:8765/api/calibrate/?ra=' + RA_HMS + '&dec=' + DEC_DMS
        #     # x = requests.post(calibrateUrl)
        #     # print("")
        #     # print(x.text)
        #     # print(x.status_code == 200)
        # except:
        #     print('todo error')  
        return await returnResponse(solve_response, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)