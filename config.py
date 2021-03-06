import machine
import json


class Config:
    def __init__(self):
        self.config_file = "config.json"
        # typical config
        self.config = {
            "scl": 21,
            "sda": 22,
            "freq": 100000,

            "dht": 15,
            # "spi": 2,
            "cs_sd": 5,

            "arduino_addr": 8,

            "multithreaded_server": False,

            "web_server": "http://192.168.0.103:8000",
            "web_token": "966259f9553c20f6620737dc334b24ee31b6ae57",
            "device_id": 5,
            # "web_server": "http://rajibweather.herokuapp.com",
            # "web_token": "56183bc84f0824cc9e325eec4258ae33742d3f64",
            # "device_id": 1,
            "delay_reading": 2000,
            "save_to_sdcard": False,

            "sta_enable": True,
            "ap_enable": False,
            "ap_ssid": "ESP32-AP",
            "ap_password": "admin1234",

            "time_sync_interval": 3600,
            "gmt": 6,
        }
        # TODO: remove this line
        # self.write_config()
        self.read_config()
        self.i2c = machine.SoftI2C(
            scl=machine.Pin(self.scl),
            sda=machine.Pin(self.sda),
            freq=self.freq
        )
        self.spi = machine.SPI(
            2,
            baudrate=80000000,
            polarity=0,
            phase=0,
            bits=8,
            firstbit=machine.SPI.MSB,
            # sck=machine.Pin(14),
            # mosi=machine.Pin(13),
            # miso=machine.Pin(12)
        )

    def write_config(self):
        print("Writing file..")
        with open(self.config_file, "wb") as f:
            json.dump(self.config, f)
        print("Done")
        self.read_config()

    def read_config(self):
        print("Reading Config file")
        try:
            with open(self.config_file, "rb") as f:
                self.config = json.load(f)
        except OSError:
            print("OS Error")
        print(self.config)

    def set(self, key, value):
        print(f"Setting {key} to {value}")
        self.config[key] = value
        self.write_config()

    def get(self, item):
        if item in self.config:
            return self.config[item]
        print(f"Could not find config.{item}")
        return None

    def __getattr__(self, item):
        if item in self.config:
            return self.config[item]
        print(f"Could not find config.{item}")
        return None


config = Config()

# _thread.allocate_lock
# acquire
# release
# exit
# start_new_thread
