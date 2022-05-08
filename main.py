import gc
import os
import time

import dht
import machine
import json

import config

try:
    import urequests as requests
except ModuleNotFoundError:
    import requests

import sdcard
# import wifimgr
import wifimngr
from ntime import Time
from bmp180 import BMP180
from lcd import lcd
import _thread

datetime = None


def main():
    lcd.putstr("    IoT Based\nWeather Station!", True, 1000)

    wifi = wifimngr.WiFi()
    wifi.connect()

    global datetime
    datetime = Time()
    print(f"Time is {datetime.datetime_str}")
    lcd.putstr(f"   {datetime.date_str}       {datetime.time_str}", True, 1000)

    # wlan = wifimgr.get_connection()
    # if wlan is None:
    # print("Could not initialize the network connection.")

    # print("WiFi OK")

    dht11 = dht.DHT11(machine.Pin(config.dht))
    # lcd.putstr("DHT")

    lcd.putstr("BMP180..", True)
    bmp180 = BMP180(config.i2c)
    bmp180.oversample_sett = 3
    lcd.putstr("BMP180 Initiated", True)

    # lcd.move_to(0, 1)
    lcd.putstr("SD Card..", x=0, y=1)
    sd = sdcard.SDCard(machine.SPI(config.spi), machine.Pin(config.cs))
    os.mount(sd, '/sd')
    # lcd.move_to(0, 1)
    lcd.putstr("SD Card Mounted", False, 500, x=0, y=1)
    print("SD Card Mounted")
    # lcd.clear()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token 966259f9553c20f6620737dc334b24ee31b6ae57'
    }
    # response = requests.post(
    #     'http://192.168.0.103:8000/api/token',
    #     headers={'Content-Type': 'application/json'},
    #     data='{"username": "rajib884", "password": "admin"}'
    # )
    # print(response.status_code)
    # print(response.content)
    lcd.putstr("", True)
    _thread.start_new_thread(xxcd, ())
    while 1:
        start = time.ticks_ms()
        bmp180.blocking_read()
        dht11.measure()
        with open(f'/sd/{datetime.date_str}.csv', 'a') as f:
            t = f"{datetime.datetime_str},{bmp180.temperature:07.4f},{bmp180.pressure:06.0f},{dht11.temperature():02d},{dht11.humidity():02d}\n"
            print(t, end="")
            f.write(t)
        data = {
            'date': datetime.datetime_str,
            'temperature': bmp180.temperature,
            'humidity': round(dht11.humidity(), 0),
            'pressure': round(bmp180.pressure, 0),
            'sensor': 5,  # choice([1, 2, 4]),
            'air_speed': 0.0,
            'air_direction': 'N',
        }
        sent = False
        try:
            response = requests.post('http://192.168.0.103:8000/api/sensors/add', headers=headers,
                                     data=json.dumps(data))
            print(response.status_code)
            print(response.content.decode())
            sent = response.status_code == 200
        except OSError:
            pass

        # lcd.clear()
        # lcd.move_to(0, 0)
        lcd.putstr(f"{chr(0)}{bmp180.temperature:04.1f}{chr(4)}C {chr(1)}{bmp180.pressure:06.0f} {chr(2)}{dht11.humidity():02d}% {'OK ' if sent else 'XX '}", x=0, y=0)
        # lcd.putstr(f"")
        # lcd.putstr(f"{chr(2)}{dht11.humidity():02d}%    ")
        # lcd.putstr(f"")
        # lcd.putstr()
        # lcd.putstr(f"{chr(3)}NaN")
        gc.collect()
        print(f"{100 * gc.mem_alloc() / (gc.mem_alloc() + gc.mem_free()):0.2f}% RAM used")
        # while time.ticks_diff(time.ticks_ms(), start) < 1900:
        #     time.sleep_ms(10)
        # lcd.backlight_off()
        while time.ticks_diff(time.ticks_ms(), start) < 2000:
            time.sleep_ms(10)
        # lcd.backlight_on()


def xxcd():
    global datetime
    while 1:
        lcd.putstr(datetime.time_str, x=8, y=1)
        time.sleep_ms(999)


if __name__ == '__main__':
    main()
