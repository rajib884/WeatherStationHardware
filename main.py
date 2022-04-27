import os
try:
    import utime as time
except:
    import time

try:
    import usocket as socket
except:
    import socket

import dht
import machine

import sdcard
# import wifimgr
from ntime import Time
from bmp180 import BMP180
from i2c_lcd import I2cLcd

led = machine.Pin(2, machine.Pin.OUT)
led.on()

i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5), freq=100000)
i2c_devices = []

n = 0
while len(i2c_devices) == 0 and n < 100:
    i2c_devices = i2c.scan()
    print(f"Found I2C devices at: {i2c_devices}")
    time.sleep(0.2)
    # print(led.value())
    led.value(not led.value())
    n += 1
    # break

if 0x27 in i2c_devices:
    print("Found LCD Display")
if 0x77 in i2c_devices:
    print("Found BMP180 Sensor")

lcd = I2cLcd(i2c, 0x27, 2, 16)

lcd.clear()
lcd.putstr("    IoT Based\nWeather Station!")

time.sleep(3)
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

while 1:
    lcd.backlight_on()
    bmp180.blocking_read()
    dht11.measure()
    with open(f'/sd/{datetime.date_str}.csv', 'a') as f:
        t = f"{datetime.datetime_str},{bmp180.temperature:07.4f},{bmp180.pressure:06.0f},{dht11.temperature():02d},{dht11.humidity():02d}\n"
        print(t, end="")
        lcd.clear()
        lcd.putstr(t[11:])
        f.write(t)
    lcd.backlight_off()
    time.sleep(2)
