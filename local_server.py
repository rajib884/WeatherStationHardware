import json

from config import config
from microdot import Microdot, Response
from wifimngr import wifi
import urequests as requests

server = Microdot()


@server.route('/')
def index(request):
    return Response.send_file('index.html')


@server.route('static/<string:file>')
def static_file(request, file):
    return Response.send_file(f'/static/{file}', headers={'Cache-Control': 'public, max-age=31536000'})


@server.route('webfonts/fa-solid-900.woff2')
def webfonts(request):
    return Response.send_file('webfonts/fa-solid-900.woff2', headers={'Cache-Control': 'public, max-age=31536000'})


@server.post('/<re:get|set|check:method>/<re:.+:target>')
def methods(request, method, target):
    if method == "get":
        return Response(str(config.get(target)), 200)
    elif method == "set":
        config.set(target, request.json)
        return Response("Success", 200)
    elif method == "check":
        if target == "web_server":
            try:
                r = requests.get(f'{request.json}/api/time', headers={'Content-Type': 'application/json'})
                return "True" if r.status_code == 200 else "False"
            except:
                return "False"
        elif target == "web_token":
            try:
                data = {"token": request.json}
                headers = {'Content-Type': 'application/json'}
                r = requests.post(f'{config.web_server}/api/check/token', headers=headers, data=json.dumps(data))
                return "True" if r.status_code == 200 else "False"
            except:
                return "False"
        elif target == "device_id":
            try:
                data = {"sensor": request.json}
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {config.web_token}'
                }
                r = requests.post(f'{config.web_server}/api/check/sensor_id', headers=headers, data=json.dumps(data))
                return "True" if r.status_code == 200 else "False"
            except:
                return "False"
        return Response("Error: Unknown target", 404)
    return Response("Error: Unknown method", 404)


@server.route('/get_ap')
def get_ap(request):
    return {
        'ap_active': "Enabled" if wifi.wlan_ap.active() else "Disabled",
        'ap_ssid': config.ap_ssid,
        'ap_password': config.ap_password,
    }


@server.post('/set_ap')
def set_ap(request):
    if "ap_ssid" in request.json:
        ssid = request.json["ap_ssid"]
    else:
        return {'error': 'SSID not provided'}, 404
    if "ap_password" in request.json:
        password = request.json["ap_password"]
        if len(password) < 8:
            return {'error': 'Invalid Password'}, 404
    else:
        return {'error': 'Password not provided'}, 404
    config.set('ap_ssid', ssid)
    config.set('ap_password', password)
    wifi.hotspot(wifi.wlan_ap.active())
    return {
        'ap_active': "Enabled" if wifi.wlan_ap.active() else "Disabled",
        'ap_ssid': config.ap_ssid,
        'ap_password': config.ap_password,
    }


@server.post('/set_sta')
def set_sta(request):
    if "sta_ssid" in request.json:
        ssid = request.json["sta_ssid"]
    else:
        return {'error': 'SSID not provided'}, 404
    if "sta_password" in request.json:
        password = request.json["sta_password"]
    else:
        password = None
    if password == "":
        password = None
    if password is None:
        if ssid in wifi.profiles:
            password = wifi.profiles[ssid]
    wifi.connect(ssid, password)
    return {
        'sta_active': "Enabled" if wifi.wlan_sta.active() else "Disabled",
        'sta_connected': str(wifi.wlan_sta.isconnected()),
        'sta_connected_to': wifi.wlan_sta.config('essid') if wifi.wlan_sta.isconnected() else "",
        'sta_networks': wifi.scan(),
    }


@server.route('/get_sta')
def get_sta(request):
    return {
        'sta_active': "Enabled" if wifi.wlan_sta.active() else "Disabled",
        'sta_connected': str(wifi.wlan_sta.isconnected()),
        'sta_connected_to': wifi.wlan_sta.config('essid') if wifi.wlan_sta.isconnected() else "",
        'sta_networks': wifi.scan(),
    }


@server.route('toggle/<string:target>')
def toggle(request, target):
    if target == 'hotspot':
        config.set('ap_enable', not wifi.wlan_ap.active())
        wifi.hotspot(config.ap_enable)
        return {'ap_active': "Enabled" if config.ap_enable else "Disabled"}
    elif target == 'wifi':
        wifi.wlan_sta.active(not wifi.wlan_sta.active())
        return {'sta_active': "Enabled" if wifi.wlan_sta.active() else "Disabled"}
    else:
        return {'error': 'unknown target'}, 404


@server.before_request
def print_req(request):
    print("\n\n\n\n")
    # print("client_addr: ", request.client_addr)  # ('192.168.0.107', 55642)
    print("method:", request.method)  # GET
    print("path:", request.path)  # /scan_wifi
    print("query_string:", request.query_string)  # None
    print("args:", request.args)  # {}
    print("headers:", request.headers)  # {'User-Agent': 'Mozi...
    # print("cookies:", request.cookies)
    # print("content_length:", request.content_length)  # 0
    # print(request.stream)  # <socket>
    print("body:", request.body)  # b''
    try:
        print("json:", request.json)  # None
    except:
        pass
    try:
        print("form:", request.form)  # None
    except:
        pass
