from quart import current_app
import os
import trio
import ast
from shlex import quote

from api.util import getExifTags

async def buildAnnotatedImage(image_url, light=0):
    try:
        image_path = os.path.dirname(image_url)
        image_name= os.path.splitext(os.path.basename(image_url))[0]
        dest_file= image_path + '/' + image_name + '-annotated.jpg'
        
        exif = await getExifTags(image_url)
        
        releventExif = ast.literal_eval(exif.get('UserComment'))

        
        rest = [
            str(x) for x in [
                exif.get('DateTimeOriginal'),
                releventExif.get('condition'),
                releventExif.get('temperature'),
                ("H: " + releventExif.get('humidity')) if releventExif.get('humidity') else None,
                releventExif.get('wind'),
                ("Lum: " + releventExif.get('luminance') + '%') if releventExif.get('luminance') else None,
                'ISO' + str(exif.get('ISO')) if exif.get('ISO') else None,
                'ƒ/' + str(exif.get('Aperture')) if exif.get('Aperture') else None,
            ] if x is not None
        ]
        annotate_cmd = [
            'sh',
            current_app.config['SCRIPTS_PATH'] + '/annotate.sh',
            image_url,
            dest_file,
            releventExif.get('title', ''),
            releventExif.get('moonday', ''),
            quote(
                releventExif.get('target', {}).get('ra', '') + ' ' +
                releventExif.get('target', {}).get('dec', '')
            ),
            str(light),
            '   '.join(rest)
        ]

        print('')
        print(*annotate_cmd)
        print('')

        res = await trio.run_process(annotate_cmd, capture_stdout=True, capture_stderr=True) 

        if res.stdout:
            print(res.stdout.decode())
        if res.stderr:
            print(res.stderr.decode())

        return dest_file
    except Exception as e:
        print('[ERROR buildAnnotatedImage]', e)
        return