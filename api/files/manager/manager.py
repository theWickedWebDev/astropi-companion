from quart import request, current_app
from ._blueprint import blueprint
import glob
import os
from PIL import Image
from api.util import returnResponse, returnFile, buildImageHeaders

@blueprint.route('/', defaults={'path': ''})
@blueprint.route('/<path:path>', methods=['GET'])
async def get_img(path):
    try:
        size = int(request.args.get('size', default=0))
        img_path = current_app.config['BASE_IMAGE_DIRECTORY'] + path
        headers = await buildImageHeaders(img_path)

        if (size != 0):
            tmp_img = '/tmp/' + img_path[1:].replace("/", ".")

            image = Image.open(img_path)
            image.thumbnail((size,size), Image.Resampling.LANCZOS)
            image.save(tmp_img)

            return await returnFile(tmp_img, 200, headers)
        else:
            return await returnFile(img_path, 200, headers)
    except Exception as e:
        print(e)
        return await returnResponse({ "error": e.args[0] }, 400)

@blueprint.route('/list/', defaults={'path': ''})
@blueprint.route("/list/<path:path>", methods=["GET"])
async def list_images(path):
    try:
        image_directory = current_app.config['BASE_IMAGE_DIRECTORY']

        if path:
            image_directory = image_directory + path

        if image_directory[-1] != '/':
            image_directory = image_directory + '/'
            
        _list = glob.glob(image_directory + '*', recursive=True)
        print(image_directory)
        _list.sort(key=os.path.getmtime, reverse=True) 
        _filtered_files = [x.replace(current_app.config['BASE_IMAGE_DIRECTORY'], '') for x in _list]
        filtered_files = [x for x in _filtered_files if '.' in x]
        _filtered_stacks = [x.replace(image_directory, '') for x in _list]
        filtered_stacks = [x for x in _filtered_stacks if '.' not in x]

        return await returnResponse({ "files": filtered_files, "stacks": filtered_stacks }, 200)
    except Exception as e:
        return await returnResponse({ "error": e.args[0] }, 404)
