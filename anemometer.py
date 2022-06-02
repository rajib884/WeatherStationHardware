from machine import Pin
from config import config


class Anemometer:
    def __init__(self):
        self.dic = {
            0b000: "N",
            0b100: "NE",
            0b101: "E",
            0b001: "SE",
            0b011: "S",
            0b111: "SW",
            0b110: "W",
            0b010: "NW",
        }
        self.t = None
        self.speed = 0.0
        self.cardinal = "N"
    
    def update(self):
        try:
            t = config.i2c.readfrom(config.arduino_addr, 5)
        except:
            self.speed = 0.0
            self.cardinal = "N"
            return
        # self.speed = (t[0] << 8 | t[1] << 8 | t[2]) << 8 | t[3]
        self.cardinal = self.dic[t[4]]

    # @property
    # def cardinal(self):
    #     # return self.dic[((not self.ir_1.value()) << 1 | (not self.ir_2.value())) << 1 | (not self.ir_3.value())]
    #     return self.dic[self.t[4]]
    
    # @property
    # def speed(self):
    #     return ((t[0] << 8 | t[1] << 8 | t[2]) << 8 | t[3]) << 8 | t[4]


anemometer = Anemometer()
