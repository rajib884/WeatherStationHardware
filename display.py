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
        self.debug = False

        self.display_width = 220
        self.display_height = 176

        self.offset_x = 4
        self.offset_y = 4
        self.height = 20 + 1
        self.width = 11

        self.cpos_x = 0
        self.cpos_y = 0
        self.lock = _thread.allocate_lock()

        self.tft.init()
        self.splash_title()
        self.tft.rotation(1)

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
        if py > self.display_height:
            self.clear()
            y = 0
            py = self.offset_y
        self.lock.acquire()
        if self.debug:
            self.tft.fillrect((px, py), (len(text) * self.width, self.height), 0x1f)
        self.tft.text((px, py), text, nowrap=True)
        self.lock.release()

        self.cpos_x = 0
        self.cpos_y = y + 1

    def make_layout(self):
        self.clear()
        icon = self.icon
        if config.sta_enable:
            icon('imgbuf/wifi.imgbuf', 0, 0)
        else:
            icon('imgbuf/wifi-slash.imgbuf', 0, 0)
        if config.ap_enable:
            icon('imgbuf/signal-stream.imgbuf', 2, 0)
        else:
            icon('imgbuf/signal-stream-slash.imgbuf', 2, 0)
        icon('imgbuf/battery-bolt.imgbuf', 4, 0)
        icon('imgbuf/clock.imgbuf', 9, 0)

        icon('imgbuf/temperature-half.imgbuf', 1, 1)
        icon('imgbuf/droplet.imgbuf', 14, 1)
        icon('imgbuf/water-arrow-down.imgbuf', 1, 2)
        icon('imgbuf/fan.imgbuf', 1, 3)
        icon('imgbuf/compass.imgbuf', 14, 3)
        icon('imgbuf/server.imgbuf', 0, 5)
        self.print("Menu", x=0, y=7)

    def icon(self, file, x, y):
        self.lock.acquire()
        if self.debug:
            self.tft.fillrect((self.offset_x + self.width * x, self.offset_y + self.height * y), (2 * self.width, self.height), 0x1f)
        self.tft.show_imgbuf(
            file,
            (self.offset_x + self.width * x, self.offset_y + self.height * y)
        )
        self.lock.release()

    # def skip_line(self):
    #     self.cpos_x = 0
    #     self.cpos_y += 1

    def clear(self):
        self.lock.acquire()
        self.tft.clear()
        self.lock.release()
        self.cpos_x = 0
        self.cpos_y = 0


display = Display()
