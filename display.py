import _thread
import machine

from ILI9225 import TFT
from config import config


class Display:
    tft = TFT(machine.SPI(
        1,
        baudrate=80000000,
        polarity=0,
        phase=0,
        bits=8,
        firstbit=machine.SPI.MSB,
        sck=machine.Pin(14),
        mosi=machine.Pin(13),
        miso=machine.Pin(12)
    ), aDC=26, aReset=27, aCS=12)

    def __init__(self):
        self.offset_x = 4
        self.offset_y = 5
        self.height = 15
        self.width = 8

        self.cpos_x = 0
        self.cpos_y = 0
        self.lock = _thread.allocate_lock()

        self.tft.init()
        self.splash_title()

    def splash_title(self):
        self.lock.acquire()
        self.tft.show_imgbuf('imgbuf/splash.imgbuf')
        self.lock.release()

    def print(self, text: str, overwrite=False, x: int = None, y: int = None, fill=False, center=False):
        if overwrite:
            self.cpos_y = max(0, self.cpos_y - 1)

        if x is None:
            x = self.cpos_x
        if y is None:
            y = self.cpos_y

        if fill and center:
            text = f"{text:^21}"
        elif fill and not center:
            text = f"{text:21}"
        elif not fill and center:
            x = (21 - len(text)) // 2

        px = self.width * x + self.offset_x
        py = self.height * y + self.offset_y
        self.lock.acquire()
        self.tft.text((px, py), text, nowrap=True)
        self.lock.release()

        self.skip_line()

    def make_layout(self):
        self.clear()
        icon = self.icon
        if config.sta_enable:
            icon('imgbuf/wifi.imgbuf', 0, 0)
        else:
            icon('imgbuf/wifi-slash.imgbuf', 0, 0)
        if config.ap_enable:
            icon('imgbuf/signal-stream.imgbuf', 3, 0)
        else:
            icon('imgbuf/signal-stream-slash.imgbuf', 3, 0)
        icon('imgbuf/battery-bolt.imgbuf', 6, 0)
        icon('imgbuf/clock.imgbuf', 11, 0)

        icon('imgbuf/temperature-half.imgbuf', 1, 2)
        icon('imgbuf/droplet.imgbuf', 14, 2)
        icon('imgbuf/water-arrow-down.imgbuf', 1, 3)
        icon('imgbuf/fan.imgbuf', 1, 4)
        icon('imgbuf/compass.imgbuf', 14, 4)
        icon('imgbuf/server.imgbuf', 0, 10)
        self.print("Menu", x=0, y=13)

    def icon(self, file, x, y):
        self.lock.acquire()
        self.tft.show_imgbuf(
            file,
            (self.offset_x + self.width * x, self.offset_y + self.height * y)
        )
        self.lock.release()

    def skip_line(self):
        self.cpos_x = 0
        self.cpos_y += 1

    def clear(self):
        self.lock.acquire()
        self.tft.clear()
        self.lock.release()
        self.cpos_x = 0
        self.cpos_y = 0


display = Display()
