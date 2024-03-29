import machine
import time
import socket
import struct
import urequests as requests

from config import config


class Time:
    def __init__(self) -> None:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        self.NTP_DELTA = 3155673600
        # The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
        self.ntp_host = "pool.ntp.org"

        self._last_updated = 0
        # self.update()

    def ntp_time(self):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(self.ntp_host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        return val - self.NTP_DELTA + config.gmt * 3600

    def set_time(self):
        t = self.ntp_time()
        tm = time.gmtime(t)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

    @staticmethod
    def set_time_from_api():
        r = requests.get(f'{config.web_server}/api/time', headers={'Content-Type': 'application/json'})
        if r.status_code == 200:
            tm = time.gmtime(int(r.content.decode()))
            machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

    def time(self):
        self._update()
        return time.time()

    @property
    def datetime_str(self):
        self._update()
        tm = time.localtime()
        # Year-Month-Day HH:MM:SS
        return f"{tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}"

    @property
    def date_str(self):
        self._update()
        tm = time.localtime()
        # Year-Month-Day
        return f"{tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d}"

    @property
    def time_str(self):
        self._update()
        tm = time.localtime()
        # HH:MM:SS
        return f"{tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}"

    def _update(self, force=False):
        if force or time.time() - self._last_updated > config.time_sync_interval:
            # TODO: lcd print ?
            try:
                print("Synchronizing time with API")
                self.set_time_from_api()
                self._last_updated = time.time()
                return
            except BaseException as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("Synchronization Failed")

            try:
                print("Synchronizing time with NTP")
                self.set_time()
                self._last_updated = time.time()
                return
            except:
                print("Synchronization Failed")

    def update(self):
        self._update(True)


datetime = Time()
