import time
import network
from display import display
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
        connected = False
        if not config.sta_enable:
            self.wlan_sta.active(False)
        else:
            display.print("Connecting to Wifi..")
            if self.wlan_sta.isconnected():
                display.print("Wifi Connected", x=2)
            else:
                self.wlan_sta.active(True)
                networks = self.wlan_sta.scan()
                current_line = display.cpos_y
                for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
                    ssid = ssid.decode('utf-8')
                    print(f"ssid: {ssid} chan: {channel} rssi: {rssi} authmode: {self.authmode.get(authmode, '?')}")
                    display.print(ssid, x=2, y=current_line, fill=True)
                    if authmode > 0:
                        if ssid in self.profiles:
                            connected = self.connect(ssid=ssid, password=self.profiles[ssid])
                    else:
                        continue
                        # don't connect to open wifi
                        # connected = self._connect(ssid, None)
                    if connected is not False:
                        display.print("Wifi Connected", x=2)
                        break
                    else:
                        display.print("Failed to connect", x=2)

        if config.ap_enable or not connected:
            display.print("Starting Hotspot")
            # Turn on wifi hotspot
            self.hotspot(True)
            display.print("Hotspot Started")
        else:
            self.hotspot(False)
            display.print("Hotspot off")
        return connected

    def scan(self):
        networks = self.wlan_sta.scan()
        r = []
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            bssid = ".".join(list(str(hex(y))[2:] for y in bssid))
            authmode = self.authmode.get(authmode, '?')
            r.append({
                'ssid': ssid,
                'bssid': bssid,
                'channel': channel,
                'rssi': rssi,
                'authmode': authmode,
                'hidden': hidden,
            })
        return r

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
