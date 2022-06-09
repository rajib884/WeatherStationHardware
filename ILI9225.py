# driver for Sainsmart 1.8" TFT display ST7735
# Translated by Guy Carver from the ST7735 sample code.
# Modirfied for micropython-esp32 by boochow
import math
import os

import machine
import time

import micropython

from config import config
from customfont import font


# # @micropython.native
def clamp(aValue, aMin, aMax):
    return max(aMin, min(aMax, aValue))


# @micropython.native
def TFTColor(aR, aG, aB):
    # Create a 16 bit rgb value from the given R,G,B from 0-255.
    # This assumes rgb 565 layout and will be incorrect for bgr.
    return ((aR & 0xF8) << 8) | ((aG & 0xFC) << 3) | (aB >> 3)


def split_i16(i):
    return [(i >> 8) & 0xFF, i & 0xFF]


class TFT(object):

    @staticmethod
    def color(aR, aG, aB):
        # Create a 565 rgb TFTColor value
        return TFTColor(aR, aG, aB)

    def __init__(self, spi, aDC, aReset, aCS):
        # aLoc SPI pin location is either 1 for 'X' or 2 for 'Y'.
        # aDC is the DC pin and aReset is the reset pin.
        self._size = (176, 220)
        self.rotate = 0  # Vertical with top toward pins.
        self.dc = machine.Pin(aDC, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.reset = machine.Pin(aReset, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.cs = machine.Pin(aCS, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.cs(1)
        self.spi = spi
        self.colorData = bytearray(2)
        self.windowLocData = bytearray(4)

        self.text_color = 0xffff
        # self.background_color = 0x1f  # Blue
        self.background_color = 0x198a

    def size(self):
        return self._size

    # #   @micropython.native
    # def on(self, aTF=True):  #todo
    #     '''Turn display on or off.'''
    #     self._writecommand(TFT.DISPON if aTF else TFT.DISPOFF)

    # #   @micropython.native
    # def invertcolor(self, aBool):  #todo
    #     '''Invert the color data IE: Black = White.'''
    #     self._writecommand(TFT.INVON if aBool else TFT.INVOFF)

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

    #  @micropython.native
    def pixel(self, aPos, aColor):
        # Draw a pixel at the given position
        if 0 <= aPos[0] < self._size[0] and 0 <= aPos[1] < self._size[1]:
            self._setwindowpoint(aPos)
            self._pushcolor(aColor)

    # @micropython.native
    def text(self, aPos, aString, aColor=None, aFont=None, aSize=1, nowrap=False, aBG=None):
        # Draw a text at the given position.  If the string reaches the end of the
        # display it is wrapped to aPos[0] on the next line.  aSize may be an integer
        # which will size the font uniformly on w,h or a or any type that may be
        # indexed with [0] or [1].

        if aColor is None:
            aColor = self.text_color
        if aBG is None:
            aBG = self.background_color

        # Make a size either from single value or 2 elements.
        if (type(aSize) == int) or (type(aSize) == float):
            wh = (aSize, aSize)
        else:
            wh = aSize

        if aFont is None:
            fw = 5
            fh = 8
        else:
            fw = aFont["Width"]
            fh = aFont["Height"]

        px, py = aPos
        w = wh[0] * fw + 1
        char = self.char2
        for c in aString:
            if aFont is None:
                char((px, py), c, aColor, wh, aBG)
            else:
                self.char((px, py), c, aColor, aFont, wh, aBG)
            px += w
            # We check > rather than >= to let the right (blank) edge of the
            # character print off the right of the screen.
            if px + w > self._size[0]:
                if nowrap:
                    break
                else:
                    py += fh * wh[1] + 1
                    px = aPos[0]

    # @micropython.native
    def char(self, aPos, aChar, aColor, aFont, aSizes, aBG=0):
        # Draw a character at the given position using the given font and color.
        # aSizes is a tuple with x, y as integer scales indicating the
        # # of pixels to draw for each pixel in the character.

        if aFont is None:
            return

        startchar = aFont['Start']
        endchar = aFont['End']

        ci = ord(aChar)
        if startchar <= ci <= endchar:
            fontw = aFont['Width']
            fonth = aFont['Height']
            ci = (ci - startchar) * fontw

            charA = aFont["Data"][ci:ci + fontw]
            px = aPos[0]
            if aSizes[0] <= 1 and aSizes[1] <= 1:
                buf = bytearray(2 * fonth * fontw)
                for q in range(fontw):
                    c = charA[q]
                    for r in range(fonth):  # 0, 1 ,2 ,3 ,4 ,5 ,6 ,7
                        if c & 0x01:
                            pos = 2 * (r * fontw + q)
                            buf[pos] = aColor >> 8
                            buf[pos + 1] = aColor & 0xff
                        else:
                            pos = 2 * (r * fontw + q)
                            buf[pos] = aBG >> 8
                            buf[pos + 1] = aBG & 0xff
                        c >>= 1
                self.image(aPos[0], aPos[1], aPos[0] + fontw - 1, aPos[1] + fonth - 1, buf)
            else:
                for c in charA:
                    py = aPos[1]
                    fillrect = self.fillrect
                    for r in range(fonth):
                        if c & 0x01:
                            fillrect((px, py), aSizes, aColor)
                        else:
                            fillrect((px, py), aSizes, aBG)
                        py += aSizes[1]
                        c >>= 1
                    px += aSizes[0]

    # @micropython.native
    def char2(self, aPos, aChar, aColor, aSizes, aBG=None):
        # Draw a character at the given position using the given font and color.
        # aSizes is a tuple with x, y as integer scales indicating the
        # # of pixels to draw for each pixel in the character.
        if aBG is None:
            aBG = self.background_color

        startchar = 0  # 0
        endchar = 254  # 254

        ci = ord(aChar)
        if startchar <= ci <= endchar:
            fontw = 5
            fonth = 8
            ci = (ci - startchar) * fontw  # 458

            charA = bytearray(font[ci:ci + fontw])  # bytearray(['0x20', '0x54', '0x54', '0x78', '0x40'])
            px = aPos[0]  # 0
            if aSizes[0] <= 1 and aSizes[1] <= 1:
                buf = bytearray(2 * fonth * fontw)  # 80 byte buffer
                for q in range(fontw):  # 0, 1, 2, 3, 4
                    c = charA[q]  # 0x20
                    for r in range(fonth):  # 0, 1 ,2 ,3 ,4 ,5 ,6 ,7
                        if c & 0x01:
                            pos = 2 * (r * fontw + q)
                            buf[pos] = aColor >> 8
                            buf[pos + 1] = aColor & 0xff
                        else:
                            pos = 2 * (r * fontw + q)
                            buf[pos] = aBG >> 8
                            buf[pos + 1] = aBG & 0xff
                        c >>= 1
                self.image(aPos[0], aPos[1], aPos[0] + fontw - 1, aPos[1] + fonth - 1, buf)
            else:
                for c in charA:
                    py = aPos[1]
                    fillrect = self.fillrect
                    for r in range(fonth):
                        if c & 0x01:
                            fillrect((px, py), aSizes, aColor)
                        else:
                            fillrect((px, py), aSizes, aBG)
                        py += aSizes[1]
                        c >>= 1
                    px += aSizes[0]

    #   @micropython.native
    def line(self, aStart, aEnd, aColor):
        # Draws a line from aStart to aEnd in the given color.  Vertical or horizontal
        # lines are forwarded to vline and hline.
        if aStart[0] == aEnd[0]:
            # Make sure we use the smallest y.
            pnt = aEnd if (aEnd[1] < aStart[1]) else aStart
            self.vline(pnt, abs(aEnd[1] - aStart[1]) + 1, aColor)
        elif aStart[1] == aEnd[1]:
            # Make sure we use the smallest x.
            pnt = aEnd if aEnd[0] < aStart[0] else aStart
            self.hline(pnt, abs(aEnd[0] - aStart[0]) + 1, aColor)
        else:
            px, py = aStart
            ex, ey = aEnd
            dx = ex - px
            dy = ey - py
            inx = 1 if dx > 0 else -1
            iny = 1 if dy > 0 else -1

            dx = abs(dx)
            dy = abs(dy)
            pixel = self.pixel
            if dx >= dy:
                dy <<= 1
                e = dy - dx
                dx <<= 1
                while px != ex:
                    pixel((px, py), aColor)
                    if e >= 0:
                        py += iny
                        e -= dx
                    e += dy
                    px += inx
            else:
                dx <<= 1
                e = dx - dy
                dy <<= 1
                while py != ey:
                    pixel((px, py), aColor)
                    if e >= 0:
                        px += inx
                        e -= dy
                    e += dx
                    py += iny

    #   @micropython.native
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

    #   @micropython.native
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

    #   @micropython.native
    def rect(self, aStart, aSize, aColor):
        # Draw a hollow rectangle.  aStart is the smallest coordinate corner
        # and aSize is a tuple indicating width, height.
        self.hline(aStart, aSize[0], aColor)
        self.hline((aStart[0], aStart[1] + aSize[1] - 1), aSize[0], aColor)
        self.vline(aStart, aSize[1], aColor)
        self.vline((aStart[0] + aSize[0] - 1, aStart[1]), aSize[1], aColor)

    #   @micropython.native
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

    #   @micropython.native
    def circle(self, aPos, aRadius, aColor):
        x, y = aPos

        self.colorData[0] = aColor >> 8
        self.colorData[1] = aColor

        f = 1 - aRadius
        ddF_x = 1
        ddF_y = -2 * aRadius
        x1 = 0
        y1 = aRadius

        self._setwindowpoint((x, y + aRadius))
        self._writedata(self.colorData)
        dp = self.Draw_Pixel

        dp(x, y + aRadius)
        dp(x, y - aRadius)
        dp(x + aRadius, y)
        dp(x - aRadius, y)
        while x1 < y1:
            if f >= 0:
                y1 -= 1
                ddF_y += 2
                f += ddF_y
            x1 += 1
            ddF_x += 2
            f += ddF_x

            dp(x + x1, y + y1)
            dp(x - x1, y + y1)
            dp(x + x1, y - y1)
            dp(x - x1, y - y1)
            dp(x + y1, y + x1)
            dp(x - y1, y + x1)
            dp(x + y1, y - x1)
            dp(x - y1, y - x1)

    # @micropython.native
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

    # @micropython.native
    def fillcircle(self, aPos, aRadius, aColor, corename=3, delta=0):
        x, y = aPos
        radius = aRadius

        self.colorData[0] = aColor >> 8
        self.colorData[1] = aColor

        vline = self.vline
        vline((x, y - radius), 2 * radius + 1, aColor)
        x0 = x
        y0 = y
        r = radius

        f = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x = 0
        y = r

        while x < y:
            if f >= 0:
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x
            if corename & 0x1:
                vline((x0 + x, y0 - y), 2 * y + 1 + delta, aColor)
                vline((x0 + y, y0 - x), 2 * x + 1 + delta, aColor)
            if corename & 0x2:
                vline((x0 - x, y0 - y), 2 * y + 1 + delta, aColor)
                vline((x0 - y, y0 - x), 2 * x + 1 + delta, aColor)

    # @micropython.native
    def fill(self, aColor=None):
        # Fill screen with the given color.
        if aColor is None:
            aColor = self.background_color
        self.fillrect((0, 0), self._size, aColor)

    # @micropython.native
    def clear(self):
        self.fillrect((0, 0), self._size, self.background_color)

    # @micropython.native
    def image(self, x0, y0, x1, y1, data):
        self._setwindowloc((x0, y0), (x1, y1))
        self._writedata(data)

    # def setvscroll(self, tfa, bfa):
    #     ''' set vertical scroll area '''
    #     self._writecommand(TFT.VSCRDEF)
    #     data2 = bytearray([0, tfa])
    #     self._writedata(data2)
    #     data2[1] = 162 - tfa - bfa
    #     self._writedata(data2)
    #     data2[1] = bfa
    #     self._writedata(data2)
    #     self.tfa = tfa
    #     self.bfa = bfa

    # def vscroll(self, value):
    #     a = value + self.tfa
    #     if (a + self.bfa > 162):
    #         a = 162 - self.bfa
    #     self._vscrolladdr(a)

    # def _vscrolladdr(self, addr):
    #     self._writecommand(TFT.VSCSAD)
    #     data2 = bytearray([addr >> 8, addr & 0xff])
    #     self._writedata(data2)

    #   @micropython.native
    def _setColor(self, aColor):
        self.colorData[0] = aColor >> 8
        self.colorData[1] = aColor
        self.buf = bytes(self.colorData) * 32

    #   @micropython.native
    def _draw(self, aPixels):
        # Send given color to the device aPixels times.
        write = self.spi.write
        cs = self.cs

        self.dc(1)
        cs(0)
        for i in range(aPixels // 32):
            write(self.buf)
        rest = (int(aPixels) % 32)
        if rest > 0:
            buf2 = bytes(self.colorData) * rest
            write(buf2)
        cs(1)

    # @micropython.native
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

    # @micropython.native
    def _setwindowloc(self, aPos0, aPos1):
        x1, y1 = aPos0  # 0, 0
        x2, y2 = aPos1  # 219, 175
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

    # @micropython.native
    def _writecommand(self, aCommand):
        # Write given command to the device.
        cs = self.cs
        self.dc(0)
        cs(0)
        self.spi.write(bytearray([aCommand]))
        cs(1)

    # @micropython.native
    def _writedata(self, aData):
        # Write given data to the device.  This may be
        # either a single int or a bytearray of values.
        cs = self.cs
        self.dc(1)
        cs(0)
        self.spi.write(aData)
        cs(1)

    # @micropython.native
    def _pushcolor(self, aColor):
        # Push given color to the device.
        self.colorData[0] = aColor >> 8
        self.colorData[1] = aColor
        self._writedata(self.colorData)

    # @micropython.native
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

    # @micropython.native
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

    # @micropython.native
    def register(self, cmd, data):
        write = self.spi.write
        dc = self.dc
        cs = self.cs

        dc(0)
        cs(0)
        write(bytearray([cmd]))
        dc(1)
        write(bytearray(split_i16(data)))
        cs(1)

    # def show_bmp(self, file, aPos=(0, 0)):
    #     # https://en.wikipedia.org/wiki/BMP_file_format
    #     with open(file, 'rb') as f:
    #         f.seek(0xA)
    #         starts_at = int.from_bytes(f.read(4), 'little')
    #         f.seek(0x12)
    #         w = int.from_bytes(f.read(4), 'little')
    #         h = int.from_bytes(f.read(4), 'little')
    #         l = w * h * 2
    #         print(f"sa: {hex(starts_at)}, {starts_at}\n{w}x{h}")
    #         # self._setwindowloc(aPos, (aPos[0]+width, aPos[1]+height))
    #         self._setwindowloc(aPos, (aPos[0] + w, aPos[1] + h))
    #         f.seek(starts_at)
    #         self.dc(1)
    #         self.cs(0)
    #         buf = bytearray(32)
    #         for _ in range(l // 32):
    #             f.readinto(buf)
    #             self.spi.write(buf)
    #         f.readinto(buf)
    #         self.spi.write(buf[:l % 30])
    #         self.cs.value(1)

    # @micropython.native
    def show_imgbuf(self, file, aPos=(0, 0)):
        with open(file, 'rb') as f:
            width = int.from_bytes(f.read(1), 'little')
            height = int.from_bytes(f.read(1), 'little')
            print(f"{width}x{height}")
            l = width * height * 2
            self._setwindowloc(aPos, (aPos[0] + width - 1, aPos[1] + height - 1))
            self.dc(1)
            self.cs(0)
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


tft = TFT(config.spi, aDC=16, aReset=17, aCS=4)
tft.init()
# tft.fill(0x1f)
tft.fill(0x198a)
tft.rotation(0)


# def test():
#     x, y = 0, 0
#     max_h = 0
#     for file in os.listdir():
#         if file[-7:] == '.imgbuf':
#             w, h = tft.show_imgbuf(file, (x, y))
#             x += w + 1
#             max_h = max(h, max_h)
#             if x > 160:
#                 y += max_h
#                 x = 0
#                 max_h = 0
#     time.sleep_ms(1000)


# test()
# tft.fillrect((0, 0), (170, 200), random.randrange(0, 0xFFFF))

# for i in range(4):
#     tft.rotation(i)
#     tft.text((10, 10), f"Hello There {i}", random.randrange(0xFFFF), sysfont)
#     tft.text((10, 30), "Hi..", random.randrange(0xFFFF), sysfont)

# tft.text((10, 100), f"Hello There", 0xFFFF, aSize=2, aBG=TFT.BLUE)
# tft.text((10, 130), "Hi..", 0xFFFF, aBG=TFT.BLUE)
