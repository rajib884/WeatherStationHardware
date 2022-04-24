from bmp180 import BMP180
from lcd_api import LcdApi
from i2c_lcd import I2cLcd

import machine, sdcard, os, dht
import time

bus =  machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5), freq=100000)   # on esp8266
print(f"Found I2C devices at: {bus.scan()}")
while 0:
    print(f"Found I2C devices at: {bus.scan()}")
    time.sleep(1)

lcd = I2cLcd(bus, 0x27, 2, 16)
lcd.clear()
lcd.putstr("Welcome!")

bmp180 = BMP180(bus)
bmp180.oversample_sett = 2

dht11 = dht.DHT11(machine.Pin(2))

sd = sdcard.SDCard(machine.SPI(1), machine.Pin(15))
os.mount(sd, '/sd')
print("Mounted SD Card")
while 1:
    bmp180.blocking_read()
    dht11.measure() 
    with open('/sd/Sensor Data.csv', 'a') as f:
        t = f"{bmp180.temperature},{bmp180.pressure},{dht11.temperature():3.1f},{dht11.humidity():3.1f}\n"
        print(t)
        lcd.clear()
        lcd.putstr(t)
        f.write(t)
    time.sleep(2)
