import subprocess

def getLuminanceFromUrl(url):
    try:
        lum = subprocess.run([
            'convert',
            url,
            '-colorspace',
            'gray',
            '-format',
            '%[fx:100*mean]',
            'info:'
        ], capture_output=True)
        
        lum_val = float(lum.stdout.decode())
        
        return lum_val
    except Exception as e:
        print(e)
        return 