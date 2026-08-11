"""
Water Quality Monitor - Pico 2
RO Parameters - OLED di GP6(SDA), GP7(SCL)
TDS Recalibrated: 0.800V → 169 ppm
ALL IN ONE
"""

import time
import math
from machine import Pin, ADC, I2C
from micropython import const
import framebuf

# ============================================================
# 📊 DRIVER OLED
# ============================================================

SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def write_data(self, buf):
        self.i2c.writeto(self.addr, bytearray([0x40]) + buf)

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00, SET_MEM_ADDR, 0x00,
            SET_DISP_START_LINE | 0x00, SET_SEG_REMAP | 0x01,
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08, SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.width > 2 * self.height else 0x12,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL, 0x30, SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON, SET_NORM_INV,
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def show(self):
        x0, x1 = 0, self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

# ============================================================
# 📊 PARAMETER RO
# ============================================================

PH_MIN = 6.5
PH_MAX = 8.5
TDS_MAX = 200.0
NTU_MAX = 6.0
TEMP_MIN = 20.0
TEMP_MAX = 30.0
NTU_JERNIH_MAX = 5.0

# ============================================================
# 📊 KALIBRASI pH
# ============================================================

V4 = 3.261
PH4 = 4.00

V7 = 2.778
PH7 = 6.86

V9 = 2.387
PH9 = 9.18

def get_ph(volt):
    if volt >= V7:
        ph = PH4 + (PH7 - PH4) * (V4 - volt) / (V4 - V7)
    else:
        ph = PH7 + (PH9 - PH7) * (V7 - volt) / (V7 - V9)
    
    if volt < 0.1:
        return 7.0
    
    return max(0, min(14, ph))

# ============================================================
# 📊 KALIBRASI TDS - REKALIBRASI
# ============================================================

# Data kalibrasi:
# 0.50V → 0 ppm (offset)
# 0.800V → 169 ppm (dari data Anda)
# 1.00V → 400 ppm (estimasi)

TDS_OFFSET_VOLT = 0.50
TDS_SLOPE = 169 / (0.800 - 0.50)  # 169 / 0.30 = 563.33

def calculate_tds(voltage, temp=25.0):
    """Konversi voltase ke TDS dengan kalibrasi linear"""
    if voltage <= TDS_OFFSET_VOLT:
        return 0
    tds = TDS_SLOPE * (voltage - TDS_OFFSET_VOLT)
    
    # Batasi nilai
    if tds < 0:
        tds = 0
    if tds > 9999:
        tds = 9999
    return tds

# ============================================================
# 📊 KALIBRASI TURBIDITY
# ============================================================

NILAI_JERNIH = 2030
NILAI_KERUH = 200
RANGE_NILAI = NILAI_JERNIH - NILAI_KERUH

def adc_to_ntu(adc):
    if adc >= NILAI_JERNIH:
        return 0.0
    elif adc <= NILAI_KERUH:
        return 100.0
    else:
        return (NILAI_JERNIH - adc) * 100.0 / RANGE_NILAI

def get_turbidity_status(ntu):
    if ntu <= 1:
        return "SANGAT JERNIH"
    elif ntu <= 5:
        return "JERNIH"
    elif ntu <= 20:
        return "AGAK KERUH"
    elif ntu <= 50:
        return "KERUH"
    else:
        return "SANGAT KERUH"

# ============================================================
# 🔬 INISIALISASI
# ============================================================

print("🔧 Inisialisasi OLED di GP6(SDA), GP7(SCL)...")
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)

devices = i2c.scan()
print(f"  Perangkat I2C: {[hex(d) for d in devices]}")

if 0x3C in devices:
    oled = SSD1306(128, 64, i2c)
    oled_ok = True
    print("  ✅ OLED terdeteksi!")
else:
    oled = None
    oled_ok = False
    print("  ❌ OLED tidak terdeteksi!")

print("🔧 Inisialisasi ADC...")
adc_ph = ADC(Pin(26))
adc_tds = ADC(Pin(27))
adc_turb = ADC(Pin(28))
print("✅ Semua siap!")

# ============================================================
# 🔬 FUNGSI BACA SENSOR
# ============================================================

def baca_ph_avg(samples=30):
    total = 0
    for _ in range(samples):
        total += adc_ph.read_u16()
        time.sleep_ms(2)
    raw = total / samples
    volt = raw * 3.3 / 65535
    ph = get_ph(volt)
    return ph, volt, raw

def baca_tds_avg(samples=30):
    total = 0
    for _ in range(samples):
        total += adc_tds.read_u16()
        time.sleep_ms(2)
    raw = total / samples
    volt = raw * 3.3 / 65535
    tds = calculate_tds(volt, 25.0)
    return tds, volt, raw

def baca_turb_avg(samples=30):
    total = 0
    for _ in range(samples):
        total += adc_turb.read_u16()
        time.sleep_ms(2)
    raw = total / samples
    raw_int = int(raw)
    adc_12bit = raw_int >> 4
    ntu = adc_to_ntu(adc_12bit)
    volt = raw * 3.3 / 65535
    return ntu, volt, raw

# ============================================================
# 📊 LOGIKA LAYAK/TIDAK LAYAK
# ============================================================

def is_water_layak(ph, tds, ntu, temp):
    return (ph >= PH_MIN and ph <= PH_MAX) and \
           (tds <= TDS_MAX) and \
           (ntu <= NTU_MAX) and \
           (temp >= TEMP_MIN and temp <= TEMP_MAX)

def get_unlayak_reason(ph, tds, ntu, temp):
    reasons = []
    
    if ph < PH_MIN or ph > PH_MAX:
        reasons.append(f"pH ({ph:.2f})")
    
    if tds > TDS_MAX:
        reasons.append(f"TDS ({tds:.0f} ppm)")
    
    if ntu > NTU_MAX:
        reasons.append(f"Kekeruhan ({ntu:.1f} NTU)")
    
    if temp < TEMP_MIN or temp > TEMP_MAX:
        reasons.append(f"Suhu ({temp:.1f}C)")
    
    if not reasons:
        return "Semua parameter normal"
    return ", ".join(reasons)

# ============================================================
# 📊 HITUNG SKOR = PERSENTASE KEJERNIHAN
# ============================================================

def hitung_persen_jernih(ntu):
    if ntu <= NTU_JERNIH_MAX:
        return 100
    elif ntu >= NTU_MAX:
        return 0
    else:
        persen = 100 - ((ntu - NTU_JERNIH_MAX) / (NTU_MAX - NTU_JERNIH_MAX) * 100)
        return max(0, min(100, int(persen)))

# ============================================================
# 🖥️ TAMPILAN OLED
# ============================================================

def draw_degree(x, y):
    if not oled_ok:
        return
    oled.pixel(x, y, 1)
    oled.pixel(x+2, y, 1)
    oled.pixel(x, y+2, 1)
    oled.pixel(x+2, y+2, 1)
    oled.pixel(x+1, y+1, 1)

def splash_screen():
    if not oled_ok:
        return
    
    oled.fill(0)
    oled.text("Water Monitor", 15, 15, 1)
    oled.text("   Quality", 20, 35, 1)
    oled.show()
    time.sleep(1.5)

def tampil_oled(ph, tds, layak, skor, temp):
    if not oled_ok:
        return
    
    oled.fill(0)
    
    oled.text(f"pH:{ph:.2f}", 0, 2, 1)
    oled.text("|", 62, 2, 1)
    oled.text(f"ppm:{tds:.0f}", 75, 2, 1)
    
    status_text = "LAYAK" if layak else "TIDAK LAYAK"
    x = (128 - len(status_text) * 8) // 2
    oled.text(status_text, x, 20, 1)
    
    oled.hline(0, 36, 128, 1)
    
    oled.text(f"{skor:.0f}%", 0, 52, 1)
    
    temp_str = f"{temp:.1f}"
    temp_x = 128 - 44
    oled.text(temp_str, temp_x, 52, 1)
    degree_x = temp_x + (len(temp_str) * 8)
    draw_degree(degree_x, 50)
    oled.text("C", degree_x + 3, 52, 1)
    
    oled.show()

# ============================================================
# 🕐 STABILISASI
# ============================================================

STABIL_DURASI = 10

def proses_stabilisasi():
    print(f"\n⏳ Stabilisasi {STABIL_DURASI} detik...")
    print("=" * 70)
    print("  Waktu  |   pH   | pH Volt |  TDS  | TDS Volt |  NTU")
    print("=" * 70)
    
    ph_list = []
    tds_list = []
    ntu_list = []
    
    for i in range(STABIL_DURASI):
        ph, ph_volt, _ = baca_ph_avg(30)
        tds, tds_volt, _ = baca_tds_avg(30)
        ntu, turb_volt, _ = baca_turb_avg(30)
        
        ph_list.append(ph)
        tds_list.append(tds)
        ntu_list.append(ntu)
        
        if i % 2 == 0:
            sisa = STABIL_DURASI - i
            ph_avg = sum(ph_list) / len(ph_list)
            tds_avg = sum(tds_list) / len(tds_list)
            ntu_avg = sum(ntu_list) / len(ntu_list)
            print(f"  t-{sisa:2d}s | {ph_avg:6.2f} |  {ph_volt:.3f}V  | {tds_avg:5.0f} |   {tds_volt:.3f}V  | {ntu_avg:5.1f}")
        
        time.sleep(0.5)
    
    ph_akhir = sum(ph_list) / len(ph_list)
    tds_akhir = sum(tds_list) / len(tds_list)
    ntu_akhir = sum(ntu_list) / len(ntu_list)
    
    print("=" * 70)
    print(f"\n✅ Selesai! pH={ph_akhir:.2f}, TDS={tds_akhir:.0f} ppm, NTU={ntu_akhir:.1f}")
    return ph_akhir, tds_akhir, ntu_akhir

# ============================================================
# 🚀 MAIN PROGRAM
# ============================================================

print("=" * 50)
print("🌊 WATER QUALITY MONITOR")
print(f"pH: {PH_MIN}-{PH_MAX} | TDS: 0-{TDS_MAX:.0f} | NTU: 0-{NTU_MAX:.0f}")
print(f"TDS Calibration: {TDS_OFFSET_VOLT}V → 0 ppm, 0.800V → 169 ppm")
print("=" * 50)

splash_screen()

temp = 25.0

while True:
    try:
        ph, tds, ntu = proses_stabilisasi()
        
        layak = is_water_layak(ph, tds, ntu, temp)
        alasan = get_unlayak_reason(ph, tds, ntu, temp)
        turb_status = get_turbidity_status(ntu)
        
        skor = hitung_persen_jernih(ntu)
        
        tampil_oled(ph, tds, layak, skor, temp)
        
        print("-" * 50)
        print("📊 HASIL FINAL:")
        print(f"   pH : {ph:.2f}  ({PH_MIN}-{PH_MAX})")
        print(f"   TDS: {tds:.0f} ppm  (0-{TDS_MAX:.0f})")
        print(f"   NTU: {ntu:.1f}  (0-{NTU_MAX:.0f}) - {turb_status}")
        print(f"   Kejernihan: {skor:.0f}%")
        print(f"   Status: {'LAYAK ✅' if layak else 'TIDAK LAYAK ❌'}")
        if alasan and alasan != "Semua parameter normal":
            print(f"   Alasan: {alasan}")
        print("-" * 50)
        
        print("\n✅ Selesai! Hasil di OLED.")
        print("Tekan RESET untuk baca ulang.\n")
        
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🔴 Berhenti")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(1)
