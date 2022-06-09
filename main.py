import gc
import os
import sys
import time

import dht
import machine
import json
import _thread

from config import config
from display import display
from req import http_post

try:
    import urequests as requests
except ModuleNotFoundError:
    import requests

import sdcard
from ntime import datetime
from anemometer import anemometer
from bmp180 import BMP180
from wifimngr import wifi
from local_server import server

file_lock = _thread.allocate_lock()
p12 = machine.Pin(12, machine.Pin.OUT)
p13 = machine.Pin(13, machine.Pin.IN)
p12.value(1)

try:
    os.remove("to_send.json")
    print("Removes 'to_send.json")
    display.print("Removed previous temp files")
except:
    pass


# if p13.value():
#     print("\n\nPin 13 is not low, exiting..\n\n")
#     sys.exit()

# def TFTColor(R, G, B):
#     return ((R & 0xF8) << 8) | ((G & 0xFC) << 3) | (B >> 3)


def main():
    display.print('IoT Based Weather Station!', x=0, y=0, center=True, fill=True)
    display.next_line()

    wifi.initialize()
    display.next_line()

    display.print(f"{'Starting Server'}")
    _thread.start_new_thread(server.run, ())
    display.print(f"Server Started at", x=2)
    if wifi.wlan_sta.isconnected():
        display.print(f"WiFi {wifi.wlan_sta.ifconfig()[0]}:5000", x=2)
    else:
        display.print('WiFi  ---', x=2)
    if wifi.wlan_ap.active():
        display.print(f"Hotspot {wifi.wlan_ap.ifconfig()[0]}:5000", x=2)
    else:
        display.print('Hotspot  ---', x=2)
    display.next_line()

    gc.collect()
    display.print("SD Card..")
    sd = sdcard.SDCard(config.spi, machine.Pin(config.cs_sd))
    os.mount(sd, '/sd')
    # lcd.move_to(0, 1)
    display.print("SD Card Mounted", overwrite=True)
    print("SD Card Mounted")

    dht11 = dht.DHT11(machine.Pin(config.dht))
    display.print("DHT..")
    while 1:
        try:
            dht11.measure()
            break
        except:
            display.print("DHT Error..", overwrite=True)
            time.sleep_ms(100)
    display.print("DHT Initiated", overwrite=True)

    display.print("BMP180..")
    bmp180 = BMP180(config.i2c)
    bmp180.oversample_sett = 3
    display.print("BMP180 Initiated", overwrite=True)
    display.next_line()

    display.print('Getting time', )
    datetime.update()
    print(f"Time is {datetime.datetime_str}")
    display.print(datetime.date_str, x=2)
    display.print(datetime.time_str, x=2)

    # lcd.clear()

    # response = requests.post(
    #     'http://192.168.0.103:8000/api/token',
    #     headers={'Content-Type': 'application/json'},
    #     data='{"username": "rajib884", "password": "admin"}'
    # )
    # print(response.status_code)
    # print(response.content)
    gc.collect()
    display.print(f"{100 * gc.mem_alloc() / (gc.mem_alloc() + gc.mem_free()):0.2f}% RAM used")
    time.sleep_ms(2000)
    display.clear()
    _thread.start_new_thread(show_time, ())
    _thread.start_new_thread(send_data, ())
    while 1:
        start = time.ticks_ms()
        bmp180.blocking_read()
        dht11.measure()
        anemometer.update()
        display.lock.acquire()
        with open(f'/sd/{datetime.date_str}.csv', 'a') as f:
            t = f"{datetime.datetime_str},{bmp180.temperature:07.4f},{bmp180.pressure:06.0f},{dht11.temperature():02d},{dht11.humidity():02d},{anemometer.cardinal}\n"
            print(t, end="")
            f.write(t)
        display.lock.release()

        file_lock.acquire()
        try:
            f = open("to_send.json", "r+")
            f.seek(-1, 2)
            f.write(",")
        except OSError:
            f = open("to_send.json", "w")
            f.write("[")
        f.write(json.dumps({
            'date': datetime.datetime_str,
            'temperature': bmp180.temperature,
            'humidity': int(round(dht11.humidity(), 0)),
            'pressure': int(round(bmp180.pressure, 0)),
            'sensor': config.device_id,
            'air_speed': 0.0,
            'air_direction': anemometer.cardinal,
        }))
        f.write("]")
        f.close()
        file_lock.release()

        display.print(
            f"{chr(0)}{bmp180.temperature:04.1f}{chr(4)}C {chr(1)}{bmp180.pressure / 101325:06.4f} {chr(2)}{dht11.humidity():02d}%{chr(3)}{anemometer.speed:3.1f} {anemometer.cardinal:<2}",
            x=0, y=0)
        gc.collect()
        print(f"{100 * gc.mem_alloc() / (gc.mem_alloc() + gc.mem_free()):0.2f}% RAM used")

        while time.ticks_diff(time.ticks_ms(), start) < config.delay_reading:
            time.sleep_ms(100)


def show_time():
    while 1:
        display.print(datetime.time_str, center=True, y=1)
        if wifi.wlan_sta.isconnected():
            display.print(f"{wifi.wlan_sta.ifconfig()[0]}:5000", center=True, fill=True, y=2)
        else:
            display.print('---', center=True, y=2, fill=True)
        if wifi.wlan_ap.active():
            display.print(f"{wifi.wlan_ap.ifconfig()[0]}:5000", center=True, fill=True, y=3)
        else:
            display.print('---', center=True, fill=True, y=3)
        time.sleep_ms(500)


def send_data():
    while 1:
        time.sleep_ms(config.delay_sending)
        try:
            os.stat("to_send.json")
        except OSError:
            print("No data available")
            time.sleep_ms(100)
            continue

        display.print(f"Sending..", x=0, y=4, fill=True)
        error = True
        # data = []
        # more_to_send = False
        # file_lock.acquire()
        # with open("to_send.json", "r") as f:
        #     lines_read = 0
        #     for line in f.readlines():
        #         lines_read += 1
        #         data.append(json.loads(line.strip()))
        #         if lines_read >= config.max_line_send:
        #             more_to_send = True
        #             break
        # file_lock.release()
        # if len(data) > 0:
        #     try:
        #         headers = {
        #             'Content-Type': 'application/json',
        #             'Authorization': f'Token {config.web_token}'
        #         }
        #         response = requests.post(
        #             f'{config.web_server}/api/sensors/add',
        #             headers=headers,
        #             data={}
        #         )
        #         print(response.status_code)
        #         print(response.content.decode())
        #         sent = response.status_code == 200
        #     except OSError:
        #         pass
        # else:
        #     error = False
        if wifi.wlan_sta.isconnected():
            try:
                response, status_code = http_post(f'{config.web_server}/api/sensors/add', "to_send.json", file_lock)
                if status_code == "200":
                    error = False
            except:
                print("Error in http_post")
        display.print('  Error' if error else '  Sent', y=4, fill=True)


if __name__ == '__main__':
    main()
