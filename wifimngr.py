import time
import network
from lcd import lcd
from config import config


class WiFi:
    def __init__(self):
        self.ap_authmode = 3  # WPA2-PSK
        self.NETWORK_PROFILES = "wifi.dat"

        self.wlan_ap = network.WLAN(network.AP_IF)  # hotspot
        self.wlan_sta = network.WLAN(network.STA_IF)  # wifi
        # self.connected = self.wlan_sta.isconnected()

        self.authmode = {
            0: "open",
            1: "WEP",
            2: "WPA-PSK",
            3: "WPA2-PSK",
            4: "WPA/WPA2-PSK"
        }
        self.profiles = {}
        self.read_profiles()

    def initialize(self):
        lcd.putstr("Starting Hotspot", True)
        # Turn on wifi hotspot
        self.hotspot(True)
        lcd.putstr("Hotspot Started", wait_ms=200, x=0, y=1)

        lcd.putstr("Connecting Wifi", True)
        if self.wlan_sta.isconnected():
            lcd.putstr("Wifi Connected ", True, 200)
            return

        connected = False
        self.wlan_sta.active(True)
        networks = self.wlan_sta.scan()

        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            print(f"ssid: {ssid} chan: {channel} rssi: {rssi} authmode: {self.authmode.get(authmode, '?')}")
            lcd.putstr(' ' * 16, x=0, y=1)
            lcd.putstr(ssid[:16], x=0, y=1)
            if authmode > 0:
                if ssid in self.profiles:
                    connected = self.connect(ssid=ssid, password=self.profiles[ssid])
            else:
                continue
                # don't connect to open wifi
                # connected = self._connect(ssid, None)
            if connected is not False:
                lcd.putstr("Wifi Connected ", wait_ms=200, x=0, y=0)
                break
        return connected

    def read_profiles(self):
        try:
            with open(self.NETWORK_PROFILES) as f:
                for line in f:
                    ssid, password = line.strip("\n").split(";")
                    self.profiles[ssid] = password
        except OSError:
            pass

    def write_profiles(self, profiles=None):
        if profiles is None:
            profiles = {}
        for ssid, password in profiles.items():
            self.profiles[ssid] = password
        lines = []
        for ssid, password in self.profiles.items():
            lines.append("%s;%s\n" % (ssid, password))
        with open(self.NETWORK_PROFILES, "w") as f:
            f.write(''.join(lines))

    def connect(self, ssid, password):
        self.wlan_sta.active(True)
        if self.wlan_sta.isconnected():
            if self.wlan_sta.config('essid') == ssid:
                return True
            else:
                self.wlan_sta.disconnect()

        print(f'Trying to connect...\nSSID:{ssid}')
        print(f'Password:{password[:3]}{"*" * (len(password) - 3)}')
        connected = False
        self.wlan_sta.connect(ssid, password)
        for retry in range(100):
            connected = self.wlan_sta.isconnected()
            if connected:
                break
            time.sleep_ms(100)
            print('.', end='')
        if connected:
            print('\nConnected. Network config: ', self.wlan_sta.ifconfig())
            self.write_profiles({ssid: password})
        else:
            print('\nFailed. Not Connected to: ' + ssid)
        return connected

    def hotspot(self, target=True):
        self.wlan_ap.active(target)
        if target:
            self.wlan_ap.config(
                essid=config.ap_ssid,
                password=config.ap_password,
                authmode=self.ap_authmode
            )


wifi = WiFi()
