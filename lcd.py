import _thread

import machine
import time

from config import config
from i2c_lcd import I2cLcd


def add_lcd_chars():
    print("Adding LCD Chars")
    lcd_chars = [
        [0x04, 0x0A, 0x0A, 0x0A, 0x0E, 0x1F, 0x1F, 0x0E],  # thermometer
        [0x0E, 0x0E, 0x0E, 0x1F, 0x0E, 0x04, 0x01, 0x1E],  # pressure
        [0x04, 0x0E, 0x0A, 0x11, 0x11, 0x1B, 0x0E, 0x00],  # humidity
        [0x00, 0x19, 0x0B, 0x04, 0x1A, 0x13, 0x00, 0x00],  # air speed
        [0x0E, 0x0A, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00],  # degree
    ]
    for i, c in enumerate(lcd_chars):
        lcd.custom_char(i, c)
    while 1:
        lcd.custom_char(0, [0x04, 0x0A, 0x0A, 0x0A, 0x0E, 0x1F, 0x1F, 0x0E])
        lcd.custom_char(1, [0x0E, 0x0E, 0x0E, 0x1F, 0x0E, 0x04, 0x01, 0x1E])
        lcd.custom_char(2, [0x00, 0x04, 0x0E, 0x0A, 0x11, 0x11, 0x1B, 0x0E])
        time.sleep_ms(500)
        lcd.custom_char(0, [0x04, 0x0A, 0x0E, 0x0E, 0x0E, 0x1F, 0x1F, 0x0E])
        lcd.custom_char(1, [0x0E, 0x0E, 0x1F, 0x0E, 0x04, 0x00, 0x01, 0x1E])
        lcd.custom_char(2, [0x04, 0x0E, 0x0A, 0x11, 0x11, 0x1B, 0x0E, 0x00])
        time.sleep_ms(500)


def wait_for_lcd():
    print("Configuring LCD")
    led = machine.Pin(2, machine.Pin.OUT)
    led.on()
    while 1:
        i2c_devices = config.i2c.scan()
        print(f"Found I2C devices at: {i2c_devices}")
        if 0x27 in i2c_devices:
            break
        led.value(not led.value())
        time.sleep_ms(200)

    if 0x27 in i2c_devices:
        print("Found LCD Display")
    if 0x77 in i2c_devices:
        print("Found BMP180 Sensor")
    led.on()
    return I2cLcd(config.i2c, 0x27, 2, 16)


lcd = wait_for_lcd()
# lcd = GpioLcd(
#     rs_pin=machine.Pin(33),
#     enable_pin=machine.Pin(25),
#     d4_pin=machine.Pin(26),
#     d5_pin=machine.Pin(27),
#     d6_pin=machine.Pin(14),
#     d7_pin=machine.Pin(13),
#     num_lines=2, num_columns=16
# )
_thread.start_new_thread(add_lcd_chars, ())
