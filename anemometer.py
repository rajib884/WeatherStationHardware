import time
from config import config
from math import pi


class Anemometer:
    def __init__(self):
        self.l = 20  # arm length (cm)
        self.directions = ["N", "NE", "E","SE", "S","SW","W","NW"]
        self.speed = 0.0
        self.cardinal = "N"
        self.last_reading = None

    def update(self):

        try:
            t = config.i2c.readfrom(config.arduino_addr, 3)
            self.cardinal = self.directions[t[2]]
            if self.last_reading is None:
                self.speed = 0.0
            else:
                c = t[0] << 8 | t[1]  # rotation count
                self.speed = self.l*c*pi*9/(time.ticks_diff(time.ticks_ms(), self.last_reading))
            self.last_reading = time.ticks_ms()
        except:
            self.speed = 0.0
            self.cardinal = "N"
            self.last_reading = None

    # @property
    # def cardinal(self):
    #     # return self.dic[((not self.ir_1.value()) << 1 | (not self.ir_2.value())) << 1 | (not self.ir_3.value())]
    #     return self.dic[self.t[4]]

    # @property
    # def speed(self):
    #     return ((t[0] << 8 | t[1] << 8 | t[2]) << 8 | t[3]) << 8 | t[4]


anemometer = Anemometer()
