import os
import time

import dht
import machine
import json
try:
    import urequests as requests
except ModuleNotFoundError:
    import requests

import sdcard
# import wifimgr
import wifimngr
from ntime import Time
from bmp180 import BMP180
from i2c_lcd import I2cLcd


def main():
    led = machine.Pin(2, machine.Pin.OUT)
    led.on()

    i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5), freq=100000)
    i2c_devices = []

    for _ in range(100):
        i2c_devices = i2c.scan()
        print(f"Found I2C devices at: {i2c_devices}")
        if len(i2c_devices) > 1:
            break
        led.value(not led.value())
        time.sleep_ms(200)

    if 0x27 in i2c_devices:
        print("Found LCD Display")
    if 0x77 in i2c_devices:
        print("Found BMP180 Sensor")

    lcd = I2cLcd(i2c, 0x27, 2, 16)
    lcd_chars = [
        [0x04, 0x0A, 0x0A, 0x0E, 0x0E, 0x1F, 0x1F, 0x0E],  # thermometer
        [0x0E, 0x0E, 0x0E, 0x1F, 0x0E, 0x04, 0x01, 0x1E],  # pressure
        [0x04, 0x0E, 0x0A, 0x11, 0x11, 0x1B, 0x0E, 0x00],  # humidity
        [0x00, 0x19, 0x0B, 0x04, 0x1A, 0x13, 0x00, 0x00],  # air speed
        [0x0E, 0x0A, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00],  # degree
    ]
    # lcd.clear()
    for i, c in enumerate(lcd_chars):
        lcd.custom_char(i, c)
        # lcd.putchar(chr(i))

    lcd.clear()
    lcd.putstr("    IoT Based\nWeather Station!")

    time.sleep(3)
    wifi = wifimngr.WiFi()
    wifi.connect()

    datetime = Time()
    print(f"Time is {datetime.datetime_str}")
    lcd.clear()
    lcd.putstr(f"   {datetime.date_str}       {datetime.time_str}")
    time.sleep(1)
    lcd.clear()

    # wlan = wifimgr.get_connection()
    # if wlan is None:
    # print("Could not initialize the network connection.")

    # print("WiFi OK")

    lcd.putstr("BMP180..")
    bmp180 = BMP180(i2c)
    bmp180.oversample_sett = 3
    lcd.move_to(0, 0)
    lcd.putstr("BMP180 Initiated")

    dht11 = dht.DHT11(machine.Pin(2))
    # lcd.putstr("DHT")

    lcd.move_to(0, 1)
    lcd.putstr("SD Card..")
    sd = sdcard.SDCard(machine.SPI(1), machine.Pin(15))
    os.mount(sd, '/sd')
    print("Mounted SD Card")
    lcd.move_to(0, 1)
    lcd.putstr("SD Card Mounted")

    time.sleep_ms(500)
    lcd.clear()

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
            'humidity': dht11.humidity(),
            'pressure': bmp180.pressure,
            'sensor': 5,  # choice([1, 2, 4]),
            'air_speed': 0,
            'air_direction': 'N',
        }
        response = requests.post('http://192.168.0.103:8000/api/sensors/add', headers=headers, data=json.dumps(data))
        print(response.status_code)

        # lcd.backlight_off()
        # lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr(f"{chr(0)}{bmp180.temperature:04.1f}{chr(4)}C ")
        lcd.putstr(f"{chr(1)}{bmp180.pressure:06.0f} ")
        # lcd.putstr(f"{chr(2)}{dht11.humidity():02d}%    ")
        lcd.putstr(f"{chr(2)}{dht11.humidity():02d}% ")
        lcd.putstr("OK " if response.status_code == 200 else "XX ")
        # lcd.putstr(f"{chr(3)}NaN")
        lcd.putstr(datetime.time_str)
        while time.ticks_diff(time.ticks_ms(), start) < 1900:
        time.sleep_ms(10)
        lcd.backlight_on()
        while time.ticks_diff(time.ticks_ms(), start) < 2000:
            time.sleep_ms(10)


if __name__ == '__main__':
    main()
