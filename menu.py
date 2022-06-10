import time
from machine import Pin

from display import display
from rotary import Rotary
from rotary_irq_esp import RotaryIRQ


class Menu:
    def __init__(self, clk=34, dt=35, sw=32):
        self.rotary = RotaryIRQ(
            pin_num_clk=clk,
            pin_num_dt=dt,
            min_val=0,
            max_val=5,
            reverse=False,
            range_mode=Rotary.RANGE_BOUNDED,
            pull_up=False,
            half_step=True,
            invert=False
        )
        self.waiting = False
        self.takenover = False
        self.options = []

        self.cursor_pos = 0

        self.led = Pin(2, Pin.OUT)
        self.sw = Pin(sw, Pin.IN, Pin.PULL_UP)
        self.sw.irq(
            trigger=Pin.IRQ_RISING,
            handler=self.trigger_waiting
        )

    def trigger_waiting(self, pin):
        self.waiting = True
        print("Interrupt..")

    @staticmethod
    def clear():
        display.lock.acquire()
        display.tft.fillrect((0, 5 + 15), (176, 220 - 5 - 15 - 60 - 5), 0x00)
        display.lock.release()

    def draw_menu(self):
        self.clear()
        for i, option in enumerate(self.options):
            display.print(option, x=3, y=i + 2)

    def draw_cursor(self):
        lpos = self.cursor_pos
        cpos = self.rotary.value()
        if lpos != cpos:
            display.lock.acquire()
            display.tft.fillrect(
                aStart=(4 + 8, 5 + 15 * (lpos + 2)),
                aSize=(14, 15),
                aColor=0x0
            )
            display.lock.release()
        display.icon('imgbuf/right.imgbuf', x=1, y=cpos + 2)
        self.cursor_pos = cpos

    def takeover(self):
        print("Hello!!")
        self.waiting = False
        self.takenover = True
        self.clear()
        # display.print(f"{self.rotary.value()}", x=2, y=2)
        self.options = [
            "Hello",
            "Option 1",
            "Second Option",
            "Option The Third",
            "Huh?",
            "Cancel",
        ]
        self.draw_menu()
        self.draw_cursor()
        self.waiting = False
        while not self.waiting:
            self.draw_cursor()
            time.sleep_ms(10)
        print(f"Selected {self.options[self.cursor_pos]}")
        display.print(f"Selected {self.options[self.cursor_pos]}", x=1, y=1)
        time.sleep(4)
        display.make_layout()
        self.waiting = False
        # time.sleep_ms(3000)


menu = Menu()
