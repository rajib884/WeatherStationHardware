import machine
try:
    import utime as time
except:
    import time
try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct



class Time:
    def __init__(self) -> None:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        self.NTP_DELTA = 3155673600
        # The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
        self.host = "pool.ntp.org"

        self.gmt = 6
        self.update_interval = 3600
        self._last_updated = 0
        self._update()
    
    def time(self):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(self.host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        return val - self.NTP_DELTA + self.gmt*3600
    
    def settime(self):
        t = self.time()
        tm = time.gmtime(t)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

    @property
    def now(self):
        self._update()
        return time.time()

    @property
    def now_str(self):
        self._update()
        tm = time.localtime()
        return f"{tm[2]}/{tm[1]}/{tm[0]} {tm[3]}:{tm[4]}:{tm[5]}"

    def _update(self):
        if time.time() - self._last_updated > self.update_interval:
            try:
                print("Synchronizing time with NTP")
                self.settime()
                self._last_updated = time.time()
            except:
                print("Synchronization Failed")
