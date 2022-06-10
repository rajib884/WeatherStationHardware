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
            max_val=10,
            reverse=False,
            range_mode=Rotary.RANGE_UNBOUNDED,
            pull_up=False,
            half_step=True,
            invert=False
        )
        self.waiting = False

        self.led = Pin(2, Pin.OUT)
        self.sw = Pin(sw, Pin.IN, Pin.PULL_UP)
        self.sw.irq(
            trigger=Pin.IRQ_RISING,
            handler=self.trigger_waiting
        )

    def trigger_waiting(self, pin):
        self.waiting = True

    @staticmethod
    def clear():
        display.tft.fillrect((0, 20), (176, 220-60), 0x00)

    def takeover(self):
        self.waiting = False
        self.clear()
        display.print(f"{self.rotary.value()}", x=2, y=10)


menu = Menu()
