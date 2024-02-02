from quart import make_response, send_file, current_app
from ._blueprint import blueprint
import os


@blueprint.route('/', defaults={'path': ''})
@blueprint.route('/<path:path>')
async def get_img(path):
    dir = current_app.config.get('BASE_IMAGE_DIRECTORY')
    print(dir + path)
    if (os.path.isfile(dir + path)):
        return await send_file(dir + path, mimetype='image/jpeg')
    else:
        return await make_response({}, 404)
