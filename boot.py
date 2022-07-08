# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import uos as os

import machine

# uos.dupterm(None, 1) # disable REPL on UART(0)

machine.freq(240000000)
import gc

# import webrepl
# webrepl.start()
gc.collect()
from config import config
import sdcard

sd = sdcard.SDCard(config.spi, machine.Pin(config.cs_sd))
os.mount(sd, '/sd')
gc.collect()
