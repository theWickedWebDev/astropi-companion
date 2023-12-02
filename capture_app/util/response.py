from quart import make_response, jsonify, send_file
from mimetypes import MimeTypes

async def returnResponse(data, status, headers=None):
    headers = dict() if headers is None else headers
    headers["Content-Type"] = "application/json"
    payload = dict(data)
    return await make_response(jsonify(payload), status, headers)

async def returnFile(file, status, headers=None):
    headers = dict() if headers is None else headers
    mime_type = MimeTypes().guess_type(file)
    headers["Content-Type"] = mime_type[0]
    headers["Cache-Control"] = "max-age=31536000"
    return await make_response(await send_file(file), status, headers)
