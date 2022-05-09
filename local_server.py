import json

from config import config
from microdot import Microdot, Response
from wifimngr import wifi
import urequests as requests

server = Microdot()


@server.route('/')
def index(request):
    f = open('/static/index.html')
    return Response(f, 200, {'Content-Type': 'text/html'})


@server.route('/bootstrap.bundle.min.js')
def index(request):
    f = open('/static/bootstrap.bundle.min.js')
    return Response(f, 200, {'Content-Type': 'text/javascript', 'Cache-Control': 'public, max-age=31536000'})


@server.route('/jquery-3.6.0.min.js')
def index(request):
    f = open('/static/jquery-3.6.0.min.js')
    return Response(f, 200, {'Content-Type': 'text/javascript', 'Cache-Control': 'public, max-age=31536000'})


@server.route('/bootstrap.min.css')
def index(request):
    f = open('/static/bootstrap.min.css')
    return Response(f, 200, {'Content-Type': 'text/css', 'Cache-Control': 'public, max-age=31536000'})


@server.route('/favicon.png')
def index(request):
    f = open('/static/favicon.png')
    return Response(f, 200, {'Content-Type': 'image/png', 'Cache-Control': 'public, max-age=31536000'})


@server.post('/set_server_address')
def set_server(request):
    config.set("web_server", request.json)
    return Response("Success", 200)


@server.post('/get_server_address')
def get_server(request):
    return Response(config.web_server, 200)


@server.post('/<re:get|set|check:method>/<re:.+:target>')
def methods(request, method, target):
    print(f"Method is {method}")
    print(f"target is {target}")
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


@server.route('/scan_wifi')
def scan_wifi(request):
    return wifi.wlan_sta.scan()
    # return Response(
    #     body=open("index.html"),
    #     headers={'Content-Type': 'text/html'}
    # )


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
