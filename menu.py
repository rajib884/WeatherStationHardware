import time

from machine import Pin

from config import config
from display import display
from rotary import Rotary
from rotary_irq_esp import RotaryIRQ
from wifimngr import wifi


class Menu:
    def __init__(self, clk=17, dt=16, sw=4):
        self.rotary = RotaryIRQ(
            pin_num_clk=clk,
            pin_num_dt=dt,
            min_val=0,
            max_val=3,
            reverse=True,
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
        display.tft.fillrect(
            (
                0,
                display.offset_y + display.height),
            (
                display.display_width,
                display.display_height - display.offset_y - (display.height + 1) * 4),
            0x00
        )
        display.lock.release()

    def draw_menu(self):
        self.clear()
        for i, option in enumerate(self.options):
            display.print(option, x=2, y=i + 1)

    def draw_cursor(self):
        lpos = self.cursor_pos
        cpos = self.rotary.value()
        if lpos != cpos:
            display.lock.acquire()
            display.tft.fillrect(
                aStart=(display.offset_x, display.offset_y + display.height * (lpos + 1)),
                aSize=(display.width * 2, display.height + 1),
                aColor=0x0
            )
            display.lock.release()
        display.icon('imgbuf/right.imgbuf', x=0, y=cpos + 1)
        self.cursor_pos = cpos

    def takeover(self):
        self.takenover = True
        while 1:
            self.waiting = False
            self.clear()
            self.options = [
                "Change Server",
                "Change ID",
                "Change WiFi",
                "Back",
            ]
            self.rotary.set(max_val=len(self.options) - 1)
            self.draw_menu()
            self.draw_cursor()
            while not self.waiting:
                self.draw_cursor()
                time.sleep_ms(10)
            print(f"Selected {self.options[self.cursor_pos]}")
            if self.options[self.cursor_pos] == "Change WiFi":
                self.wifi_settings()
            elif self.options[self.cursor_pos] == "Change Server":
                self.server_settings()
            elif self.options[self.cursor_pos] == "Change ID":
                self.id_settings()
            elif self.options[self.cursor_pos] == "Back":
                break
            # display.print(f"Selected {self.options[self.cursor_pos]}", x=1, y=1)
            # time.sleep(4)
        display.make_layout()
        self.waiting = False
        # time.sleep_ms(3000)

    def wifi_settings(self):
        while 1:
            self.waiting = False
            self.clear()
            self.options = [
                "Disable WiFi" if wifi.wlan_sta.isconnected() else "Enable WiFi",
                "Disable Hotspot" if wifi.wlan_ap.active() else "Enable Hotspot",
                "Back",
            ]
            self.rotary.set(max_val=len(self.options) - 1)
            self.draw_menu()
            self.draw_cursor()
            while not self.waiting:
                self.draw_cursor()
                time.sleep_ms(10)
            print(f"Selected {self.options[self.cursor_pos]}")
            if self.options[self.cursor_pos] == "Back":
                break
            else:
                if self.options[self.cursor_pos] == "Disable WiFi":
                    config.set("sta_enable", False)
                elif self.options[self.cursor_pos] == "Enable WiFi":
                    config.set("sta_enable", True)
                elif self.options[self.cursor_pos] == "Disable Hotspot":
                    config.set("ap_enable", False)
                elif self.options[self.cursor_pos] == "Enable Hotspot":
                    config.set("ap_enable", True)
                display.clear()
                wifi.initialize(current_line=1)
                display.clear()

    def id_settings(self):
        while 1:
            self.waiting = False
            self.clear()
            self.options = [
                "Increase ID",
                "Decrease ID",
                "Back",
                f"ID: {config.device_id}"
            ]
            self.rotary.set(max_val=len(self.options) - 2)
            self.draw_menu()
            self.draw_cursor()
            while not self.waiting:
                self.draw_cursor()
                time.sleep_ms(10)
            print(f"Selected {self.options[self.cursor_pos]}")
            if self.options[self.cursor_pos] == "Back":
                break
            elif self.options[self.cursor_pos] == "Increase ID":
                config.set("device_id", config.device_id + 1)
                config.reload_server = True
            elif self.options[self.cursor_pos] == "Decrease ID":
                config.set("device_id", config.device_id - 1)
                config.reload_server = True

    def server_settings(self):
        while 1:
            self.waiting = False
            self.clear()
            self.options = [
                "Online Server",
                "Local Server",
                "Back",
                f"Server: {config.web_server.split('//', 1)[1]}"
            ]
            self.rotary.set(max_val=len(self.options) - 2)
            self.draw_menu()
            self.draw_cursor()
            while not self.waiting:
                self.draw_cursor()
                time.sleep_ms(10)
            print(f"Selected {self.options[self.cursor_pos]}")
            if self.options[self.cursor_pos] == "Back":
                break
            elif self.options[self.cursor_pos] == "Online Server":
                config.set("web_server", "http://rajibweather.herokuapp.com")
                config.set("web_token", "56183bc84f0824cc9e325eec4258ae33742d3f64")
                config.reload_server = True
            elif self.options[self.cursor_pos] == "Local Server":
                t = wifi.wlan_sta.ifconfig()[0].split('.')
                self.clear()
                self.rotary.set(min_val=0, max_val=255)
                for i in range(len(t)):
                    display.print(f"Editing {i+1}th value", x=1, y=2)
                    self.waiting = False
                    self.rotary.set(value=int(t[i]))
                    while not self.waiting:
                        t[i] = str(self.rotary.value())
                        display.print('.'.join(t), x=1, y=1)
                self.rotary.set(min_val=0, max_val=3, value=2)
                config.set("web_server", f"http://{'.'.join(t)}:8000")
                config.set("web_token", "966259f9553c20f6620737dc334b24ee31b6ae57")
                config.reload_server = True


menu = Menu()
