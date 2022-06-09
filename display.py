import _thread
import time

from ILI9225 import TFT
from config import config


class Display:
    tft = TFT(config.spi, aDC=16, aReset=17, aCS=4)

    def __init__(self):
        self.offset_x = 4
        self.offset_y = 15
        self.height = 14
        self.width = 8

        self.cpos_x = 0
        self.cpos_y = 0
        self.lock = _thread.allocate_lock()

        self.tft.init()
        self.splash_title()

    def splash_title(self):
        self.lock.acquire()
        self.tft.show_imgbuf('splash.imgbuf')
        self.lock.release()
        # self.clear()
        # tft.text((38, 85), 'IOT Based', aSize=2)
        # tft.text((6, 105), 'Weather Station', aSize=2)
        time.sleep_ms(1000)
        self.clear()

    def print(self, text: str, overwrite=False, x: int = None, y: int = None, fill=False, center=False):
        if overwrite:
            self.cpos_y = max(0, self.cpos_y - 1)

        if x is None:
            x = self.cpos_x
        if y is None:
            y = self.cpos_y

        if fill and center:
            text = f"{text:^29}"
        elif fill and not center:
            text = f"{text:29}"
        elif not fill and center:
            x = (29 - len(text)) // 2

        px = self.width * x + self.offset_x
        py = self.height * y + self.offset_y
        self.lock.acquire()
        self.tft.text((px, py), text, nowrap=True)
        self.lock.release()

        self.skip_line()

    def skip_line(self):
        self.cpos_x = 0
        self.cpos_y += 1

    def clear(self):
        self.tft.clear()
        self.cpos_x = 0
        self.cpos_y = 0


display = Display()
