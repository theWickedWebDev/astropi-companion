import trio
from quart import request, current_app
from datetime import datetime
import itertools
import json
from capture_app.util import returnResponse, generateCameraConfigDict, capturePhoto, appendExif, buildImageHeaders, returnFile, buildAnnotatedImage, getExifTags

from ._blueprint import blueprint

DEFAULT_FILENAME=datetime.now().strftime("%d-%m-%Y_%H:%M:%S:%f")

camera: trio.CancelScope | None = None
capturedImage: trio.CancelScope | None = None
intervalometer: trio.CancelScope | None = None

async def create_interval(interval: float or int, func, *args, task_status=trio.TASK_STATUS_IGNORED):
    global intervalometer
    with intervalometer:
        task_status.started(intervalometer)
        while True:
            await trio.sleep(interval)
            func(*args)

@blueprint.route('/interval/stop', methods=['POST'])
async def stop_intervalometer():
    try:        
        global intervalometer

        if intervalometer:
            intervalometer.cancel()
            intervalometer = None

            return await returnResponse({ "intervalometer": "stopped" }, 200)
        else:
            return await returnResponse({ "intervalometer": "already stopped" }, 200)
            
    except Exception as e:
        print(e)
        return await returnResponse({ "capture_interval": False, "error": e.args[0] }, 404)

@blueprint.route('/interval/start/<interval>', methods=['POST'])
async def start_intervalometer(interval=10):
    try:        
        global intervalometer
        
        if intervalometer:
            return await returnResponse({ "intervalometer": "already started" }, 200)
        
        intervalometer = trio.CancelScope()
        blueprint.nursery.start_soon(create_interval, float(interval), print, "Hello")
        return await returnResponse({ "intervalometer": "started" }, 200)
            
    except Exception as e:
        print(e)
        return await returnResponse({ "intervalometer": "not started", "error": e.args[0] }, 404)

@blueprint.route('/capture/<count>', methods=['POST'])
@blueprint.route('/capture/', methods=['POST'])
async def camera_capture(count=1):
    global camera

    if camera:
        return await returnResponse({"res": "capture already in progress"}, 201)

    try:
        body = await request.json

        cameraConf = body.get('config', {})
        captureTarget = body.get('target')
        captureScripts = body.get('scripts')
        
        camera = trio.CancelScope()
        capturedImage = trio.CancelScope()
        
        with camera:
            captureRes = await capturePhoto(cameraConf)
            captureErrors = captureRes['errors']
            raw_capture = captureRes['captures']['raw']
            jpg_capture = captureRes['captures']['jpg']

            print("raw_capture", raw_capture)
            print("jpg_capture", jpg_capture)
        
        with capturedImage:
            imageList = [
                x for x in [
                    raw_capture,
                    jpg_capture,
                ] if x is not None
            ]
            await appendExif(imageList, captureTarget)

        image_dest=str
        if jpg_capture != None:
            image_dest = jpg_capture
        elif raw_capture != None:
            image_dest = raw_capture 

        if 'annotate' in captureScripts.keys():
            # Use JPG if exists, else copy/convert cr2 to JPG first
            annotationImage=str
            if jpg_capture != None:
                annotationImage = jpg_capture
            elif raw_capture != None:
                annotationImage = raw_capture 
            
            annotationLevel = 0 if captureScripts['annotate'] == "light" else 1
            print('annotationLevel')
            print(annotationLevel)
            print('')
            image_dest = await buildAnnotatedImage(annotationImage, annotationLevel)


        print('image_dest')
        print(image_dest)
        print(captureErrors)
        print('')

        headers = await buildImageHeaders(image_dest, captureErrors)

        return await returnFile(image_dest, 200, headers)
    except Exception as e:
        if camera:
            print('Cancelling camera operation due to exception...')
            camera.cancel()
            camera = None

        print(e)
        return await returnResponse({ "preview": False, "error": e.args[0] }, 404)

@blueprint.route('/cancel/', methods=['POST'])
async def cancel_camera_operation():

    global camera

    try:
        if camera:
            print('Cancelling camera operation...')
            camera.cancel()
            camera = None

            return await returnResponse({"cancelled": True }, 200)
        else:
            return await returnResponse({"cancelled": False, "message": "Nothing to cancel" }, 200)
    except Exception as e:
        print(e)
        return await returnResponse({ "cancelled": False, "error": e.args[0] }, 404)




# "DATE",
# "TARGET_NAME",
# "TARGET_RA",
# "TARGET_DEC",
# "FRAMES",
# "EXPOSURE_SECONDS",
# "FOCAL",
# "HISTOGRAM",
# "START_TIME",
# "END_TIME"         