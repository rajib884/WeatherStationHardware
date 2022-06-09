# driver for 2.2" TFT display ILI9225
import math

import machine
import time

import micropython


def clamp(aValue, aMin, aMax):
    return max(aMin, min(aMax, aValue))


def split_i16(i):
    return [(i >> 8) & 0xFF, i & 0xFF]


class TFT(object):

    def __init__(self, spi, aDC, aReset, aCS):
        # aLoc SPI pin location is either 1 for 'X' or 2 for 'Y'.
        # aDC is the DC pin and aReset is the reset pin.
        self._size = (176, 220)
        self.rotate = 0  # Vertical with top toward pins.
        self.dc = machine.Pin(aDC, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.reset = machine.Pin(aReset, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.cs = machine.Pin(aCS, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.cs.value(1)
        self.spi = spi
        self.colorData = bytearray(2)
        self.windowLocData = bytearray(4)

        self.text_color = 0xffff
        self.background_color = 0x0

    def rotation(self, aRot):
        r = aRot & 3  # rotation
        if r & 1:
            self._size = (220, 176)
        else:
            self._size = (176, 220)
        self.rotate = r
        v = 0b1000000110000
        if aRot == 1:
            v = 0b1000000101000
        elif aRot == 2:
            v = 0b1000000000000
        elif aRot == 3:
            v = 0b1000000011000
        self.register(0x03, v)
        self._setwindowloc((0, 0), self._size)
        self.vert_scroll(0, self._size[1], 0)

    def vert_scroll(self, top, scrollines, offset):
        if offset <= -scrollines or offset >= scrollines:
            offset = 0
        vsp = top + offset
        if offset < 0:
            vsp += scrollines
        sea = top + scrollines - 1
        self.register(0x32, top)
        self.register(0x31, sea)
        self.register(0x33, vsp - top)

    def text(self, aPos, aString, nowrap=False):
        fw = 8
        fh = 14
        px, py = aPos
        w = fw  # + 1
        char = self.char
        for c in aString:
            char((px, py), c)
            px += w
            if px + w > self._size[0]:
                if nowrap:
                    break
                else:
                    py += fh + 1
                    px = aPos[0]

    def char(self, aPos, aChar):
        start = 32
        end = 192
        ci = ord(aChar)
        l = 8 * 14 * 2
        buf = bytearray(14 * 2)
        if start <= ci < end:
            t = (ci - start) * l
            with open('font.imgbuf', 'rb') as f:
                f.seek(t)
                r = f.readinto
                w = self.spi.write
                self._setwindowloc(aPos, (aPos[0] + 8 - 1, aPos[1] + 14 - 1))
                self.dc.value(1)
                self.cs.value(0)
                for _ in range(8):
                    r(buf)
                    w(buf)
                self.cs.value(1)

    def vline(self, aStart, aLen, aColor):
        # Draw a vertical line from aStart for aLen. aLen may be negative.
        start = (clamp(aStart[0], 0, self._size[0]), clamp(aStart[1], 0, self._size[1]))
        stop = (start[0], clamp(start[1] + aLen, 0, self._size[1]))
        # Make sure smallest y 1st.
        if stop[1] < start[1]:
            start, stop = stop, start
        self._setwindowloc(start, stop)
        self._setColor(aColor)
        self._draw(aLen)

    def hline(self, aStart, aLen, aColor):
        # Draw a horizontal line from aStart for aLen. aLen may be negative.
        start = (clamp(aStart[0], 0, self._size[0]), clamp(aStart[1], 0, self._size[1]))
        stop = (clamp(start[0] + aLen, 0, self._size[0]), start[1])
        # Make sure smallest x 1st.
        if stop[0] < start[0]:
            start, stop = stop, start
        self._setwindowloc(start, stop)
        self._setColor(aColor)
        self._draw(aLen)

    def fillrect(self, aStart, aSize, aColor):
        # Draw a filled rectangle.  aStart is the smallest coordinate corner
        # and aSize is a tuple indicating width, height.
        start = (clamp(aStart[0], 0, self._size[0]), clamp(aStart[1], 0, self._size[1]))
        end = (clamp(start[0] + aSize[0] - 1, 0, self._size[0]), clamp(start[1] + aSize[1] - 1, 0, self._size[1]))

        if end[0] < start[0]:
            tmp = end[0]
            end = (start[0], end[1])
            start = (tmp, start[1])
        if end[1] < start[1]:
            tmp = end[1]
            end = (end[0], start[1])
            start = (start[0], tmp)

        self._setwindowloc(start, end)
        numPixels = (end[0] - start[0] + 1) * (end[1] - start[1] + 1)
        self._setColor(aColor)
        self._draw(numPixels)

    def Draw_Pixel(self, x, y):
        if self.rotate & 1:
            y, x = x, y
        reg = self.register
        for cmd, data in [
            (0x36, x),
            (0x37, x),
            (0x38, y),
            (0x39, y),
            (0x20, x),
            (0x21, y),
        ]:
            reg(cmd, math.ceil(data))
        self._writecommand(0x22)
        self._writedata(self.colorData)

    def fill(self, aColor=None):
        # Fill screen with the given color.
        if aColor is None:
            aColor = self.background_color
        self.fillrect((0, 0), self._size, aColor)

    def clear(self):
        self.fillrect((0, 0), self._size, self.background_color)

    def _setColor(self, aColor):
        self.colorData[0] = aColor >> 8
        self.colorData[1] = aColor
        self.buf = bytes(self.colorData) * 32

    def _draw(self, aPixels):
        # Send given color to the device aPixels times.
        write = self.spi.write
        cs = self.cs.value

        self.dc.value(1)
        cs(0)
        for i in range(aPixels // 32):
            write(self.buf)
        rest = (int(aPixels) % 32)
        if rest > 0:
            buf2 = bytes(self.colorData) * rest
            write(buf2)
        cs(1)

    def _setwindowpoint(self, aPos):
        # Set a single point for drawing a color to.
        x, y = aPos
        if self.rotate & 1:
            y, x = x, y
        reg = self.register
        for cmd, data in [
            (0x36, x),
            (0x37, x),
            (0x38, y),
            (0x39, y),
            (0x20, x),
            (0x21, y),
        ]:
            reg(cmd, math.ceil(data))
        self._writecommand(0x22)

    def _setwindowloc(self, aPos0, aPos1):
        x1, y1 = aPos0
        x2, y2 = aPos1
        x = x1
        y = y1
        if self.rotate & 1:
            x1, y1, x2, y2 = y1, x1, y2, x2
            x = x2
            y = y1
        reg = self.register
        for cmd, data in [
            (0x36, x2),
            (0x37, x1),
            (0x38, y2),
            (0x39, y1),
            (0x20, x),
            (0x21, y),
        ]:
            reg(cmd, math.ceil(data))
        self._writecommand(0x22)

    def _writecommand(self, aCommand):
        # Write given command to the device.
        cs = self.cs.value
        self.dc.value(0)
        cs(0)
        self.spi.write(bytearray([aCommand]))
        cs(1)

    def _writedata(self, aData):
        # Write given data to the device.  This may be
        # either a single int or a bytearray of values.
        cs = self.cs.value
        self.dc.value(1)
        cs(0)
        self.spi.write(aData)
        cs(1)

    def _reset(self):
        # Reset the device.
        dc = self.dc
        reset = self.reset
        delay = time.sleep_ms

        dc(0)
        reset(1)
        delay(500)
        reset(0)
        delay(500)
        reset(1)
        delay(500)

    def init(self):
        self._reset()
        # XC=0x20,YC=0x21,CC=0x22,RC=0x22,SC1=0x31,SC2=0x33,MD=0x03,VL=1,R24BIT=0;
        tftlcd_delay16 = micropython.const(0xFFFF)
        reg = self.register
        for cmd, data in [
            (0x01, 0x011C),
            (0x02, 0x0100),
            (0x03, 0x1030),
            (0x08, 0x0808),  # // set BP and FP
            (0x0B, 0x1100),  # // frame cycle
            (0x0C, 0x0000),  # // RGB interface setting R0Ch=0x0110 for RGB 18Bit and R0Ch=0111for RGB16Bit
            (0x0F, 0x1401),  # // Set frame rate----0801
            (0x15, 0x0000),  # // set system interface
            (0x20, 0x0000),  # // Set GRAM Address
            (0x21, 0x0000),  # // Set GRAM Address
            # //*************Power On sequence ****************//
            (tftlcd_delay16, 50),  # // delay 50ms
            (0x10, 0x0800),  # // Set SAP,DSTB,STB----0A00
            (0x11, 0x1F3F),  # // Set APON,PON,AON,VCI1EN,VC----1038
            (tftlcd_delay16, 50),  # // delay 50ms
            (0x12, 0x0121),  # // Internal reference voltage= Vci;----1121
            (0x13, 0x006F),  # // Set GVDD----0066
            (0x14, 0x4349),  # // Set VCOMH/VCOML voltage----5F60
            # //-------------- Set GRAM area -----------------//
            (0x30, 0x0000),
            (0x31, 0x00DB),
            (0x32, 0x0000),
            (0x33, 0x0000),
            (0x34, 0x00DB),
            (0x35, 0x0000),
            (0x36, 0x00AF),
            (0x37, 0x0000),
            (0x38, 0x00DB),
            (0x39, 0x0000),
            # // ----------- Adjust the Gamma Curve ----------//
            (0x50, 0x0001),  # // 0x0400
            (0x51, 0x200B),  # // 0x060B
            (0x52, 0x0000),  # // 0x0C0A
            (0x53, 0x0404),  # // 0x0105
            (0x54, 0x0C0C),  # // 0x0A0C
            (0x55, 0x000C),  # // 0x0B06
            (0x56, 0x0101),  # // 0x0004
            (0x57, 0x0400),  # // 0x0501
            (0x58, 0x1108),  # // 0x0E00
            (0x59, 0x050C),  # // 0x000E
            (tftlcd_delay16, 50),  # // delay 50ms
            (0x07, 0x1017),
            # //0x22, 0x0000,
        ]:
            if cmd == tftlcd_delay16:
                time.sleep_ms(data)
            else:
                reg(cmd, data)

    def register(self, cmd, data):
        write = self.spi.write
        dc = self.dc.value
        cs = self.cs.value

        dc(0)
        cs(0)
        write(bytearray([cmd]))
        dc(1)
        write(bytearray(split_i16(data)))
        cs(1)

    def show_imgbuf(self, file, aPos=(0, 0)):
        with open(file, 'rb') as f:
            width = int.from_bytes(f.read(1), 'little')
            height = int.from_bytes(f.read(1), 'little')
            print(f"{width}x{height}")
            l = width * height * 2
            self._setwindowloc(aPos, (aPos[0] + width - 1, aPos[1] + height - 1))
            self.dc.value(1)
            self.cs.value(0)
            # self.spi.write(f.read(l))
            buf = bytearray(64)
            r = f.readinto
            w = self.spi.write
            for _ in range(l // 64):
                r(buf)
                w(buf)
            if l % 64 > 0:
                r(buf)
                w(buf[:l % 64])
            self.cs.value(1)
        return width, height
