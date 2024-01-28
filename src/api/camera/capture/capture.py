import trio
from quart import request, current_app, session
from ... import util as u

from ._blueprint import blueprint

camera: trio.CancelScope | None = None


@blueprint.route('/', methods=['POST'])
async def capture_single_frame():
    global camera

    if camera:
        return await u.returnResponse({"res": "capture already in progress"}, 201)

    if (not session.get('active_capture_session')):
        return await u.returnResponse({"res": "no active session has been set"}, 404)

    camera = trio.CancelScope()
    with camera:
        try:
            return await u.returnResponse({"res": "captured photo"}, 200)
        except Exception as e:
            if camera:
                camera.cancel()
                camera = None
            u.logError("capture_single_frame", "Cancelling Camera", e)


@blueprint.route('/cancel/', methods=['POST'])
async def cancel_camera_operation():
    global camera

    try:
        if camera:
            camera.cancel()
            camera = None

            return await u.returnResponse({"cancelled": True}, 200)
        else:
            return await u.returnResponse({"cancelled": False, "message": "Nothing to cancel"}, 200)
    except Exception as e:
        u.logError("cancel_camera_operation", "Cancelling Camera", e)


"""
async def capture_single_frame(format="manual"):
    global camera

    if camera:
        return await returnResponse({"res": "capture already in progress"}, 201)

    camera = trio.CancelScope()
    with camera:
        try:

            body = await request.json

            bodyConfig = body.get('config', {})
            allowMismatchBodyConfig = body.get('allowMismatchConfig', [])
            captureSession = body.get('session', {})
            captureTarget = body.get('target', {})
            captureScripts = body.get('scripts', {})
            captureFormat = bodyConfig.get('format', format)

            cameraConfig, errors = generateCameraConfigDict(bodyConfig) 

            #  TODO:
            #  Delayed start/end 
            #  bodyConfig.start && bodyConfig.end
            # cron job?
            
            # VALIDATION
            try:
                validFormatTypes = ["lights", "darks", "flats", "biases"]

                if captureFormat not in validFormatTypes:
                    raise Exception([f"[{captureFormat}] is not a valid format: {' | '.join(validFormatTypes)}", 'POST /capture/$FORMAT/'])

                captureSessionId = captureSession.get('id', None)

                if (captureSessionId):
                    stack_path = f"{captureSession.get('name', 'unknown')}/{captureSessionId}"

                    if not os.path.exists(f"{current_app.config['BASE_IMAGE_DIRECTORY']}{stack_path}"):
                        raise Exception([f"[{stack_path}] does not exist", 'POST /capture/sessions/'])
                else:
                    raise Exception(["Must provide a capture session ID.", {"session": { "id": "some_id" }}])
            except Exception as e:
                camera.cancel()
                camera = None
                return await returnResponse({"message": e.args[0][0], "hint": e.args[0][1] }, 400)
            
            #  Create new stack tree
            new_stack_directory = current_app.config['BASE_IMAGE_DIRECTORY'] + stack_path
            # if not os.path.exists(new_stack_directory ):
            #     os.makedirs(f"{new_stack_directory}/{captureFormat}")
            # elif not os.path.exists(f"{new_stack_directory}/{captureFormat}"):
            #     os.makedirs(f"{new_stack_directory}/{captureFormat}")
            
            # Save/Load configuration

            camerajson=None
            try:
                if (os.path.isfile(new_stack_directory + '/camera.json')):
                    with open(new_stack_directory + '/camera.json', 'r') as f:
                        camerajson=json.loads(f.read())

                    if captureFormat == 'lights':
                        bodyCameraConfig = cameraConfig
                        currentCameraConfig, errors = generateCameraConfigDict(camerajson.get('lights', {}).get('config', {}))

                        _, _, modified, _ = dict_compare(bodyCameraConfig, currentCameraConfig)
                        _notAllowedKeys = [ i for i in modified.keys() if i not in allowMismatchBodyConfig]

                        errs = []
                        keys = set()
                        
                        if (len(_notAllowedKeys) > 0):
                            diff = []          
                            for k in _notAllowedKeys:
                                diff.append({ k: {"_original": modified[k][1], "new": modified[k][0]} })
                                keys.add(k)
                            errs.append({ "modified": diff })

                        if (len(errs) > 0):
                            raise Exception({
                                "msg": 'New configuration found',
                                "data": errs,
                                "keys": keys
                            })
                else:
                    if captureFormat == 'lights':
                        with open(new_stack_directory + '/camera.json', 'w') as f:
                            _body = body
                            del _body['allowMismatchConfig']
                            f.write(json.dumps({"id": captureSessionId, captureFormat: _body}, indent=2))

                    if captureFormat == 'darks':
                        # check if camera.json file exists using name/date and load settings and capture
                        # 
                        # 
                        cameraConfig, errors = generateCameraConfigDict(bodyConfig)
                    # if captureFormat == 'flats':
                    # check if camera.json file exists using name/date and load settings and capture
                    # if captureFormat == 'biases':
                    # Ask if should update master biases
                    # check if camera.json file exists using name/date and load settings and capture
            except Exception as e:
                camera.cancel()
                camera = None
                if (len(e.args) > 0):
                    resolveHelp={"allowMismatchConfig": list(e.args[0].get('keys')) }
                    resolveHelp.update(camerajson.get(captureFormat, {}))
                    resolveHelp.update(body)
                    return await returnResponse({"_message": e.args[0].get('msg'), "errors": e.args[0].get('data'), "hint": resolveHelp }, 400)
                else:
                    print(e)
                    
            dir = stack_path + '/' + captureFormat + '/'
            captureRes = await capturePhoto(cameraConfig, dir)
            print("\nCAPTURE RES")
            print(captureRes)
            captureErrors = captureRes.get('errors', [])
            raw_capture = captureRes.get('captures').get('raw')
            jpg_capture = captureRes.get('captures').get('jpg')
    
            imageList = [
                x for x in [
                    raw_capture,
                    jpg_capture,
                ] if x is not None
            ]
            
            if captureScripts.get('solve', False) == True:
                try:
                    solve_response = await solveField(image_url=imageList[0], returnWithData=True, returnWithPoints=True, noplots=True)
                    print(solve_response)
                except Exception as e:
                    print('[solveField] ERROR', e)
                    
            await appendExif(imageList, captureTarget)

            image_dest=str
            if jpg_capture != None:
                image_dest = jpg_capture
            elif raw_capture != None:
                image_dest = raw_capture 

            if captureScripts.get('annotate', False) == True:
                # Use JPG if exists, else copy/convert cr2 to JPG first
                annotationImage=str
                if jpg_capture != None:
                    annotationImage = jpg_capture
                elif raw_capture != None:
                    annotationImage = raw_capture 
                annotationLevel = 1 if captureScripts['annotate'] == "light" else 0

                image_dest = await buildAnnotatedImage(annotationImage, annotationLevel)

            headers = await buildImageHeaders(image_dest, captureErrors)

            if camera:
                camera.cancel()
                camera = None

            return await returnFile(image_dest, 200, headers)
        except Exception as e:
            if camera:
                camera.cancel()
                camera = None
            logError("capture_single_frame", "Cancelling Camera", e)
"""
