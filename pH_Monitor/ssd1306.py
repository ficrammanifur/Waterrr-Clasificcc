"""
MicroPython SSD1306 OLED driver for RP2350
"""

from micropython import const
import framebuf
import time

# SSD1306 Commands
_SET_CONTRAST = const(0x81)
_DISPLAY_ALL_ON_RESUME = const(0xA4)
_DISPLAY_ALL_ON = const(0xA5)
_NORMAL_DISPLAY = const(0xA6)
_INVERT_DISPLAY = const(0xA7)
_DISPLAY_OFF = const(0xAE)
_DISPLAY_ON = const(0xAF)
_SET_DISPLAY_OFFSET = const(0xD3)
_SET_COM_PINS = const(0xDA)
_SET_VCOM_DETECT = const(0xDB)
_SET_DISPLAY_CLOCK_DIV = const(0xD5)
_SET_PRECHARGE = const(0xD9)
_SET_MULTIPLEX = const(0xA8)
_SET_START_LINE = const(0x40)
_MEMORY_MODE = const(0x20)
_CHARGE_PUMP = const(0x8D)
_COM_SCAN_DEC = const(0xC8)
_SEG_REMAP_ON = const(0xA1)

class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self.init_display()
    
    def write_cmd(self, cmd):
        try:
            self.i2c.writeto(self.addr, bytes([0x00, cmd]))
            return True
        except:
            return False
    
    def write_data(self, data):
        try:
            chunk_size = 128
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                self.i2c.writeto(self.addr, bytes([0x40]) + chunk)
            return True
        except:
            return False
    
    def init_display(self):
        try:
            self.write_cmd(_DISPLAY_OFF)
            time.sleep_ms(10)
            
            init_cmds = [
                _SET_DISPLAY_CLOCK_DIV, 0x80,
                _SET_MULTIPLEX, 0x3F,
                _SET_DISPLAY_OFFSET, 0x00,
                _SET_START_LINE | 0x00,
                _CHARGE_PUMP, 0x14,
                _MEMORY_MODE, 0x00,
                _SEG_REMAP_ON,
                _COM_SCAN_DEC,
                _SET_COM_PINS, 0x12,
                _SET_CONTRAST, 0xFF,
                _SET_PRECHARGE, 0xF1,
                _SET_VCOM_DETECT, 0x40,
                _DISPLAY_ALL_ON_RESUME,
                _NORMAL_DISPLAY,
                _DISPLAY_ON
            ]
            
            for cmd in init_cmds:
                self.write_cmd(cmd)
                time.sleep_ms(1)
            
            self.fill(0)
            self.show()
            return True
            
        except Exception as e:
            print(f"OLED init error: {e}")
            return False
    
    def show(self):
        try:
            self.write_cmd(0x21)
            self.write_cmd(0)
            self.write_cmd(self.width - 1)
            
            self.write_cmd(0x22)
            self.write_cmd(0)
            self.write_cmd(self.pages - 1)
            
            self.write_data(self.buffer)
            return True
        except:
            return False
    
    def poweroff(self):
        self.write_cmd(_DISPLAY_OFF)
    
    def poweron(self):
        self.write_cmd(_DISPLAY_ON)
    
    def contrast(self, val):
        val = max(0, min(255, val))
        self.write_cmd(_SET_CONTRAST)
        self.write_cmd(val)
    
    def scroll(self, dx, dy):
        if dx != 0 or dy != 0:
            new_buffer = bytearray(len(self.buffer))
            temp_fb = framebuf.FrameBuffer(new_buffer, self.width, self.height, framebuf.MONO_VLSB)
            
            for y in range(self.height):
                for x in range(self.width):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.pixel(x, y):
                            temp_fb.pixel(nx, ny, 1)
            
            self.buffer[:] = new_buffer
    
    def text(self, string, x, y, color=1):
        super().text(string, x, y, color)
    
    def pixel(self, x, y, color=None):
        if color is None:
            return super().pixel(x, y)
        super().pixel(x, y, color)
    
    def fill(self, color):
        super().fill(color)
    
    def line(self, x1, y1, x2, y2, color):
        super().line(x1, y1, x2, y2, color)
    
    def hline(self, x, y, w, color):
        super().hline(x, y, w, color)
    
    def vline(self, x, y, h, color):
        super().vline(x, y, h, color)
    
    def rect(self, x, y, w, h, color):
        super().rect(x, y, w, h, color)
    
    def fill_rect(self, x, y, w, h, color):
        super().fill_rect(x, y, w, h, color)
