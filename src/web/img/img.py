from quart import make_response, send_file, current_app
from ._blueprint import blueprint
import os


@blueprint.route('/', defaults={'path': ''})
@blueprint.route('/<path:path>')
async def get_img(path):
    dir = current_app.config.get('BASE_IMAGE_DIRECTORY')
    print(dir + path)
    if (os.path.isfile(dir + path)):
        res = await send_file(dir + path, mimetype='image/jpeg')

        if ('thumb_' in path):
            res.headers['Pragma-directive'] = 'no-cache'
            res.headers['Cache-directive'] = 'no-cache'
            res.headers['Cache-control'] = 'no-cache'
            res.headers['Pragma'] = 'no-cache'
            res.headers['Expires'] = '0'
        return res
    else:
        return await make_response({}, 404)
