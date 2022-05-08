import machine
from micropython import const

# BMP180 and LCD display
_scl = const(21)
_sda = const(22)
_freq = const(100000)
i2c = machine.SoftI2C(scl=machine.Pin(_scl), sda=machine.Pin(_sda), freq=_freq)

# DHT
dht = const(15)

# SD Card
spi = const(2)
cs = const(5)

# _thread.allocate_lock
# acquire
# release
# exit
# start_new_thread

