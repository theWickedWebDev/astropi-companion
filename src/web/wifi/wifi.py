import trio
from quart import request, url_for, render_template_string, render_template
from ._blueprint import blueprint
import json

wifi_device = "wlan1"

'''
Workaround for non sudo:

sudo nano /etc/NetworkManager/NetworkManager.conf 

[main]
plugins=ifupdown,keyfile
auth-polkit=false

[ifupdown]
managed=false

[device]
wifi.scan-rand-mac-address=no
'''


@blueprint.route('/', methods=['POST'])
@blueprint.route('/', methods=['GET'])
async def index():
    cmd = ["nmcli", "--colors", "no", "-m", "multiline", "--get-values",
           "SSID,FREQ,IN-USE", "dev", "wifi", "list", "ifname", wifi_device]

    cap_proc = await trio.run_process(cmd, capture_stdout=True, capture_stderr=True)
    ssids_list = cap_proc.stdout.decode().split('\n')
    ssids = ssids_list[0::3]
    freq = ssids_list[1::3]
    inuse = ssids_list[2::3]
    active_wifi = ""
    options = []

    for i, ssid in enumerate(ssids):
        only_ssid = ssid.removeprefix("SSID:")
        if len(only_ssid) > 0:
            active_wifi = only_ssid if inuse[i].removeprefix(
                'IN-USE:') == '*' else active_wifi
            _freq = int(freq[i].removeprefix("FREQ:").removesuffix(' MHz'))
            if (_freq > 5000):
                _freq = "5Ghz"
            elif (_freq < 3000 and _freq > 2000):
                _freq = "2.4Ghz"
            options.append({
                "selected": inuse[i].removeprefix('IN-USE:') == '*',
                "value": only_ssid,
                "label": f"{only_ssid} // {_freq}"
            })

    if (request.method == 'POST'):
        try:
            form = await request.form
            ssid = form['ssid']  # type: ignore
            password = form['password']  # type: ignore
            connection_command = ["nmcli", "--colors", "no", "device",
                                  "wifi", "connect", ssid, "ifname", wifi_device]
            if (ssid is None or password is None):
                raise Exception('No credentials provided')

            if len(password) > 0:
                connection_command.append("password")
                connection_command.append(password)

            result = None
            result = await trio.run_process(connection_command, capture_stdout=True, capture_stderr=True)
            return await render_template(
                'pages/wifi/wifi.jinja',
                options=options,
                active=active_wifi,
                complete=True,
                success=False if result.stderr else True
            )
        except Exception as e:
            print(e)
            return await render_template(
                'pages/wifi/wifi.jinja',
                options=options,
                active=active_wifi,
                complete=True,
                success=False
            )

    return await render_template(
        'pages/wifi/wifi.jinja',
        options=options,
        active=active_wifi
    )
