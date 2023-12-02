from quart import request, current_app
from capture_app.util import returnResponse, returnFile, buildImageHeaders, buildAnnotatedImage

from ._blueprint import blueprint

@blueprint.route("/<image>/", methods=["GET"])
async def annotate_image(image):
    args = request.args

    if args:
        light = 1 if 'light' in args.keys() else 0

    try:
        image_url = buildAnnotatedImage(current_app.config['BASE_IMAGE_DIRECTORY'] + image, light)

        headers = await buildImageHeaders(image_url)

        return await returnFile(image_url, 200, headers)
    except Exception as e:
        print('[ERROR] annotate_image', e)
        return await returnResponse({ "error": e.args[0] }, 400)
    