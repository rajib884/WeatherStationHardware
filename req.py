import socket
import os
import time

import select

from config import config

headers = """\
POST /{path} HTTP/1.1\r
Content-Type: application/json\r
Content-Length: {content_length}\r
Host: {host}\r
Connection: close\r
Authorization: Token {auth}\r
\r\n"""


def http_post(url, file, lock):
    _, _, host, path = url.split('/', 3)
    if ":" in host:
        host, port = host.split(":")
    else:
        port = 80

    address = socket.getaddrinfo(host, port)[0][-1]

    s = socket.socket()
    s.settimeout(5)
    s.connect(address)

    buf = bytearray(1024)
    lock.acquire()
    head = headers.format(
        path=path,
        content_length=os.stat(file)[6],
        host=host,
        auth=config.web_token,
    ).encode('utf8')
    print(head)
    with open(file) as f:
        s.send(head)
        while 1:
            l = f.readinto(buf)
            print(l)
            if l == 0:
                break
            s.write(buf[:l])
            print(buf[:l])
    # TODO: readline blocks
    poller = select.poll()
    poller.register(s, select.POLLIN)
    res = poller.poll(1000)  # time in milliseconds
    if not res:
        # s is still not ready for input, i.e. operation timed out
        lock.release()
        print("Timeout!")
        return None, None
    _, status_code, _ = s.readline().decode().strip().split(" ", 2)
    print(status_code)
    if status_code == "200":
        print(f"removing {file}")
        os.remove(file)
    lock.release()
    while True:
        line = s.readline().decode().strip()
        print(line)
        if len(line) == 0:
            break
    print("data is:")
    data = s.read().decode()
    print(data)
    s.close()
    return data, status_code

# http_post("http://192.168.0.103:8000/api/sensors/add")
#
# sys.exit()
#
#
# def http_get(url='http://192.168.0.103/api/sensors/add', port=8000):
#     _, _, host, path = url.split('/', 3)
#     print(host)
#     print(path)
#     addr = socket.getaddrinfo(host, port)[0][-1]
#     s = socket.socket()
#     s.connect(addr)
#     body = '{"key": "val"}'
#     body_bytes = body.encode('ascii')
#     content_length = len(body_bytes)
#     s.send(bytes(
#         f'POST /{path} HTTP/1.1\r\nContent-Type: application/json\r\nContent-Length: {content_length}\r\nHost: {host}\r\nConnection: close\r\nAuthorization: Token 966259f9553c20f6620737dc334b24ee31b6ae57\r\n\r\n' + body,
#         'utf8'))
#     while True:
#         data = s.recv(100)
#         if data:
#             print(str(data, 'utf8'), end='')
#         else:
#             break
#     s.close()
#
#
# http_get()
#
#
# def http_post(url, port=80):
#     _, _, host, path = url.split('/', 3)
#     addr = socket.getaddrinfo(host, port)[0][-1]
#     s = socket.socket()
#     headers = """\
#     POST /{path} HTTP/1.1\r
#     Content-Type: application/json\r
#     Host: {host}\r
#     Connection: close\r
#     Authorization: Token 966259f9553c20f6620737dc334b24ee31b6ae57\r
#     \r\n""".format(path=path, host=host).encode('utf8')
#     s.connect(addr)
#     buf = bytearray(1024)
#     with open("to_send.json") as f:
#         while 1:
#             l = f.readinto(buf)
#             s.write(buf[:l])
#             if l == 0:
#                 break
#     while True:
#         data = s.recv(100)
#         if data:
#             print(str(data, 'utf8'), end='')
#         else:
#             break
#     s.close()
#
#
# host = "192.168.0.103"
# port = 8000
#
# headers = """\
# GET /api/sensors/ HTTP/1.1\r
# Host: 192.168.0.103:8000\r
# User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0\r
# Accept: application/json, text/javascript, */*; q=0.01\r
# Accept-Language: en-US,en;q=0.5\r
# Accept-Encoding: gzip, deflate\r
# Referer: http://192.168.0.103:8000/\r
# X-Requested-With: XMLHttpRequest\r
# Connection: keep-alive\r
# Cookie: pad=PadBlack; view=grid; font=small; csrftoken=2TI7LSOIEoxPfqjqGU047QcBTeCgUbH7GfZPqW6YcKQBAg3OfNTUGTvfZtMt4TZ8; sessionid=dk6gzbb6d4jo82vtp2g2llzmuqsczq2a\r
# \r\n"""
#
# hex = """\
# POST /check/web_server HTTP/1.1\r
# Host: 192.168.0.100:5000\r
# User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0\r
# Accept: */*\r
# Accept-Language: en-US,en;q=0.5\r
# Accept-Encoding: gzip, deflate\r
# Content-Type: application/json\r
# X-Requested-With: XMLHttpRequest\r
# Content-Length: 27\r
# Origin: http://192.168.0.100:5000\r
# Connection: keep-alive\r
# Referer: http://192.168.0.100:5000/\r
# \r\n"""
#
# """Authorization: Token 966259f9553c20f6620737dc334b24ee31b6ae57"""
#
# body = '{"key": "val"}'
# body_bytes = body.encode('ascii')
# header_bytes = headers.format(
#     content_type="application/json",
#     content_length=len(body_bytes),
#     host=str(host) + ":" + str(port)
# ).encode('iso-8859-1')
#
# payload = header_bytes + body_bytes
#
# # ...
#
# socket.sendall(payload)
