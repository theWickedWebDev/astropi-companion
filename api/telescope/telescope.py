from quart import session, current_app
from api.util import returnResponse
import numpy as np
from datetime import datetime
from astropy.coordinates import SkyCoord

from api.util import get_session_data, deep_update_telescope_file, read_telescope_file, returnResponse, generateCameraConfigDict, setCurrentConfigValue, controlTelescope, TelescopeControlMethods, capturePhoto, solveField, TelescopeTargetTypes, session_exists, appendGeneratedData, CALIBRATION_CAMERA_SETTINGS, MOCKED_LIGHT_FRAME_G1_00_JPG, MOCKED_LIGHT_FRAME_G1_01_JPG, MOCKED_LIGHT_FRAME_G1_02_JPG, MOCKED_LIGHT_FRAME_G1_03_JPG, MOCKED_LIGHT_FRAME_G1_04_JPG, MOCKED_LIGHT_FRAME_G1_05_JPG, deep_update_session

from ._blueprint import blueprint

# TODO:
@blueprint.route('/start/', methods=['POST'])
async def start_telescope():
    try:
        return await returnResponse({"started": True}, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "started": False, "error": e.args[0] }, 404)

# TODO:
@blueprint.route('/stop/', methods=['POST'])
async def stop_telescope():
    try:
        return await returnResponse({"poweroff": True}, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "poweroff": False, "error": e.args[0] }, 404)

@blueprint.route('/calibrate/', methods=['POST'])
async def calibrate_telescope():
    id = session.get('active_capture_session')
    BASE_SESSIONS_DIRECTORY = f"{current_app.config['BASE_SESSIONS_DIRECTORY']}"
    session_file = f"{BASE_SESSIONS_DIRECTORY}{id}.json"
    session_target = get_session_data(session_file).get('target', {})

    if (not id):
        return await returnResponse({
            "error": "There is no active session"
        }, 404)

    if (not session_exists(id)):
        return await returnResponse({}, 404)
    
    try:          
        TMP_CALIBRATION_FRAME_LOCATION = f"{current_app.config['TMP_CALIBRATION_FRAME_LOCATION']}"
        telescope_data = read_telescope_file()  

        # CAPTURE CALIBRATION PHOTO AND PLATESOLVE
        if (not current_app.config.get('MOCK_CAMERA_ENABLED')):
            # TODO: Use different camera settings for calibrations, perhaps a set of them
            # that you can pick +/- exposure
            camera_config, _ = generateCameraConfigDict(CALIBRATION_CAMERA_SETTINGS)
            await setCurrentConfigValue('aperture', '5.6')
            capture_res = await capturePhoto(camera_config, TMP_CALIBRATION_FRAME_LOCATION)
            calibration_img_path = capture_res.get('captures', {}).get('jpg')
        else:
            calibration_img_path = MOCKED_LIGHT_FRAME_G1_03_JPG

        try:
            solve_response = await solveField(image_url=calibration_img_path, returnWithData=True, returnWithPoints=True, noplots=True)
            
            # UPDATE SESSION JSON WITH PLATESOLVED RESPONSE
            last_plate_solve = solve_response.get('data')
            last_plate_solve.update({ 'time': datetime.now().strftime("%d-%m-%Y %H:%M:%S") })
            telescope_data = deep_update_telescope_file(data={ "last_plate_solve": last_plate_solve })

            solved_center = solve_response.get('data', {}).get('center', {}).get('hmsdms', None)
            solved_center_coords = SkyCoord(ra=solved_center.get('ra'), dec=solved_center.get('dec'))
            desired_target = SkyCoord(
                ra=session_target.get('value', {}).get('ra'),
                dec=session_target.get('value', {}).get('dec')
            )

            desired_coords_hms_dms = desired_target.to_string('hmsdms').split(' ')

            # GET DEVIATION
            ra_offset = (solved_center_coords.ra - desired_target.ra) * np.cos(desired_target.dec.to('radian'))
            dec_offset = (solved_center_coords.dec - desired_target.dec)

            tolerance = current_app.config.get('PLATE_DELTA_TOLERANCE')

            # TODO: get the values properly vs float(.to_string())
            outside_tolerance = abs(float(ra_offset.to('arcsec').to_string().split(' ')[0])) > tolerance or abs(float(dec_offset.to('arcsec').to_string().split(' ')[0])) > tolerance
                        
            deviation = {
                "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "frame_path": calibration_img_path,
                "outside_tolerance": outside_tolerance,
                "solved": {
                    "ra": solved_center_coords.ra.to_string(),
                    "dec": solved_center_coords.dec.to_string(),
                },
                "hmsdms": {
                    "ra": ra_offset.to_string(),
                    "dec": dec_offset.to_string(),
                }, 
                "arcseconds": {
                    "ra": ra_offset.to('arcsec').to_string().split(' ')[0],
                    "dec": dec_offset.to('arcsec').to_string().split(' ')[0],
                }
            }

            pushed_deviation = [deviation] + telescope_data.get('deviation', [])
            telescope_data = deep_update_telescope_file({
                    "calibrated": True,
                    "lastSolvedCoordinates": {
                        "ra": solved_center_coords.ra.to_string(),
                        "dec": solved_center_coords.dec.to_string()
                    },
                    "deviation": pushed_deviation
                })

            # SLEW AND CALIBRATE TELESCOPE TO DESIRED TARGET IF OUTSIDE OF TOLERANCE
            if (outside_tolerance):
                controlTelescope(TelescopeControlMethods.CALIBRATE.value, {
                    "key": TelescopeTargetTypes.RA_DEC.value,
                    "value": solved_center
                })  
                controlTelescope(TelescopeControlMethods.GOTO.value, { "key": "RA_DEC", "value": {
                    "ra": desired_coords_hms_dms[0],
                    "dec": desired_coords_hms_dms[1]
                }})
        except Exception as e:
            print(e.args[0])

        return await returnResponse(read_telescope_file(), 200)


    except Exception as e:
        print(e)
        return await returnResponse({"message":"There was an error calibrating the telescope", "error": e.args }, 400)
