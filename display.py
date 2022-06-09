import _thread
import time

from ILI9225 import tft


class Display:
    def __init__(self):
        self.offset_x = 4
        self.offset_y = 15
        self.height = 10
        self.width = 6

        self.cpos_x = 0
        self.cpos_y = 0
        self.lock = _thread.allocate_lock()
        self.splash_title()

    def splash_title(self):
        self.lock.acquire()
        tft.show_imgbuf('splash.imgbuf')
        self.lock.release()
        # self.clear()
        # tft.text((38, 85), 'IOT Based', aSize=2)
        # tft.text((6, 105), 'Weather Station', aSize=2)
        time.sleep_ms(1000)
        self.clear()

    def print(self, text: str, overwrite=False, x: int = None, y: int = None, fill=False, center=False, color=None):
        if overwrite:
            self.cpos_y = max(0, self.cpos_y-1)

        if x is None:
            x = self.cpos_x
        if y is None:
            y = self.cpos_y

        if fill and center:
            text = f"{text:^29}"
        elif fill and not center:
            text = f"{text:29}"
        elif not fill and center:
            x = (29 - len(text))//2

        px = self.width * x + self.offset_x
        py = self.height * y + self.offset_y
        self.lock.acquire()
        tft.text((px, py), text, aColor=color, nowrap=True)
        self.lock.release()

        self.next_line()

    def next_line(self):
        self.cpos_x = 0
        self.cpos_y += 1

    def clear(self):
        tft.clear()
        self.cpos_x = 0
        self.cpos_y = 0


display = Display()
