from quart import make_response, jsonify

async def returnResponse(data, status, headers=None):
    if headers is None:
        headers = dict()
    headers["Content-Type"] = "application/json"
    payload = dict(meta=dict(code=status), response=data)
    return await make_response(jsonify(payload), status, headers)
