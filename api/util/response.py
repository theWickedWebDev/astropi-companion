from quart import make_response, jsonify, send_file
from mimetypes import MimeTypes
from colorama import Fore, Style

async def returnResponse(payload, status, headers=None):
    headers = dict() if headers is None else headers
    headers["Content-Type"] = "application/json"
    res = await make_response(jsonify(payload), status, headers)
    return res

async def returnFile(file, status, headers=None):
    headers = dict() if headers is None else headers
    mime_type = MimeTypes().guess_type(file)
    headers["Content-Type"] = mime_type[0]
    headers["Cache-Control"] = "max-age=31536000"
    return await make_response(await send_file(file), status, headers)

def logError(title: str, msg: str, e: Exception):
    print(Fore.RED + title + ' ' + Style.DIM + Fore.RED + msg + Style.RESET_ALL)
    raise

def logMessage(msg: str, d: any):
    print(Fore.MAGENTA + str(msg) + Style.RESET_ALL)
    print(Style.DIM + str(d) + Style.RESET_ALL)

def logCommand(msg: str, d: any, cmd: any):
    print('\n' + Fore.MAGENTA + str(msg) + Style.RESET_ALL)
    print(Style.DIM + str(d) + Style.RESET_ALL)
    print(str(cmd) + '\n')