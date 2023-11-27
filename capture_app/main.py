from quart_trio import QuartTrio
from quart import request, send_file
import subprocess
import os
import json
from PIL import Image
import requests
import argparse
from dotenv import load_dotenv

from ._response import returnResponse
from .exif import exif
from .plate import platesolve
from .histogram import histogram
from .images import images
from .annotate import annotate
from .stack import stack


def create_app(mode='Development'):
    load_dotenv()
    _app = QuartTrio(__name__)
    _app.config.from_prefixed_env("QUART")
    _app.register_blueprint(images, url_prefix="/images")
    _app.register_blueprint(exif, url_prefix="/exif")
    _app.register_blueprint(platesolve, url_prefix="/solve")
    _app.register_blueprint(histogram, url_prefix="/histogram")
    _app.register_blueprint(annotate, url_prefix="/annotate")
    _app.register_blueprint(stack, url_prefix="/stack")

    return _app

app = create_app()

app.run()