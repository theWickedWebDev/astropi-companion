import requests
from quart import current_app
from .constants import TelescopeControlMethods, TelescopeTargetTypes
from .telescope import deep_update_telescope_file

def apiSlugQueryFromTarget(target):
    key = target.get('key')
    value = target.get('value')

    match key:
        case TelescopeTargetTypes.RA_DEC.value:
            slug = ''
            query = f"/?ra={value.get('ra')}&dec={value.get('dec')}"
        case TelescopeTargetTypes.BY_NAME.value:
            slug = '/by_name'
            query = f"/?name={value}"
        case _:
            slug = '/solar_system_object'
            query = f"/?name={value}"
    
    return slug, query

def controlTelescope(method, target):
    if (method not in [x.value for x in TelescopeControlMethods]):
        raise Exception(f'Telescope control method [{method}] not valid. Options: {[x.value for x in TelescopeControlMethods]}')
    
    TELESCOPE_API_URL = current_app.config['TELESCOPE_API_URL']

    slug, query = apiSlugQueryFromTarget(target)
    api_url = f"{TELESCOPE_API_URL}/{method}{slug}{query}"

    try:
        r = requests.post(api_url)
        if (r.status_code != 200):
            raise Exception(f"{method} call to telescope failed")
        else:
            if (method == TelescopeControlMethods.CALIBRATE):
                deep_update_telescope_file({ "calibrated": True})
        
        return r
    except Exception as e:
        print(e)
        raise Exception('Telescope not responding')
    