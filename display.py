import _thread
import time

from ILI9225 import TFT
from config import config


class Display:
    tft = TFT(config.spi, aDC=16, aReset=17, aCS=4)

    def __init__(self):
        self.offset_x = 4
        self.offset_y = 4
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
        self.lock.acquire()
        icon = self.tft.show_imgbuf
        w, h = self.width, self.height
        ox = self.offset_x
        oy = self.offset_y
        if config.sta_enable:
            icon('imgbuf/wifi.imgbuf', (ox, oy))
        else:
            icon('imgbuf/wifi-slash.imgbuf', (ox, oy))
        if config.ap_enable:
            icon('imgbuf/signal-stream.imgbuf', (ox + w * 3, oy))
        else:
            icon('imgbuf/signal-stream-slash.imgbuf', (ox + w * 3, oy))
        icon('imgbuf/battery-bolt.imgbuf', (ox + w * 6, oy))
        icon('imgbuf/clock.imgbuf', (ox + w * 11, oy))

        icon('imgbuf/temperature-half.imgbuf', (ox + w, oy + h*2))
        icon('imgbuf/water-arrow-down.imgbuf', (ox + w, oy + h*3))
        icon('imgbuf/droplet.imgbuf', (ox + w, oy + h*4))
        icon('imgbuf/fan.imgbuf', (ox + w, oy + h*5))
        self.lock.release()

    def skip_line(self):
        self.cpos_x = 0
        self.cpos_y += 1

    def clear(self):
        self.tft.clear()
        self.cpos_x = 0
        self.cpos_y = 0


display = Display()
