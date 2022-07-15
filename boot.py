# This file is executed on every boot (including wake-boot from deepsleep)

import gc

import machine
import uos as os

from config import config

# import webrepl
# import esp
# esp.osdebug(None)

machine.freq(240000000)
gc.collect()

# webrepl.start()
# uos.dupterm(None, 1) # disable REPL on UART(0)

if config.save_to_sdcard:
    import sdcard

    # sd = sdcard.SDCard(config.spi, machine.Pin(config.cs_sd), baudrate=18000000)
    sd = sdcard.SDCard(config.spi, machine.Pin(config.cs_sd))
    os.mount(sd, '/sd')
    print("SD Card Mounted")
    gc.collect()
