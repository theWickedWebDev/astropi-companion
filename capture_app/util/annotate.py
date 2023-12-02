from quart import current_app
import os
import trio
import ast
from shlex import quote

from capture_app.util import getExifTags

async def buildAnnotatedImage(image_url, light=0):
    try:
        image_path = os.path.dirname(image_url)
        image_name= os.path.splitext(os.path.basename(image_url))[0]
        dest_file= image_path + '/' + image_name + '-annotated.jpg'

        exif = await getExifTags(image_url)
        releventExif = ast.literal_eval(exif['UserComment'])

        annotate_cmd = [
            'sh',
            current_app.config['SCRIPTS_PATH'] + '/annotate.sh',
            image_url,
            dest_file,
            releventExif['title'],
            releventExif['moonday'],
            quote(releventExif['target']['ra'] + ' ' + releventExif['target']['dec']),
            str(light),
            '   '.join([
                exif['DateTimeOriginal'],
                releventExif['condition'],
                releventExif['temperature'],
                "H: " + releventExif['humidity'],
                releventExif['wind'],
                "Lum: " + releventExif['luminance'] + '%',
                str(exif['ISO']),
                str(exif['Aperture'])
            ])
        ]

        res = await trio.run_process(annotate_cmd, capture_stdout=True, capture_stderr=True) 

        if res.stdout:
            print(res.stdout.decode())
        if res.stderr:
            print(res.stderr.decode())

        return dest_file
    except Exception as e:
        print('[ERROR buildAnnotatedImage]', e)
        return