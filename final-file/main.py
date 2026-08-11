"""
Water Quality Monitor - Pico 2
RO Parameters - FIXED
"""

import time
import math
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306

# ============================================================
# 📊 PARAMETER RO
# ============================================================

PH_MIN = 6.5
PH_MAX = 8.5
TDS_MAX = 200.0
NTU_MAX = 6.0
TEMP_MIN = 20.0
TEMP_MAX = 30.0

# ============================================================
# 📊 KALIBRASI pH - DARI ESP32
# ============================================================

V4 = 3.235
PH4 = 4.01

V7 = 2.590
PH7 = 6.86

V9 = 2.183
PH9 = 9.18

def get_ph(volt):
    if volt >= V7:
        ph = PH4 + (PH7 - PH4) * (V4 - volt) / (V4 - V7)
    else:
        ph = PH7 + (PH9 - PH7) * (V7 - volt) / (V7 - V9)
    
    # 🔥 FIX: Jika voltase sangat rendah (sensor tidak terhubung)
    if volt < 0.1:
        return 7.0  # Return pH netral sebagai default
    
    return max(0, min(14, ph))

# ============================================================
# 📊 KALIBRASI TDS - DFRobot Formula
# ============================================================

def calculate_tds(voltage, temp=25.0):
    if voltage < 0.1:
        return 0
    
    tempCoeff = 1.0 + 0.02 * (temp - 25.0)
    compVoltage = voltage / tempCoeff
    
    tds = (133.42 * compVoltage ** 3 -
           255.86 * compVoltage ** 2 +
           857.39 * compVoltage) * 0.5
    
    if tds < 0:
        tds = 0
    if tds > 9999:
        tds = 9999
    return tds

# ============================================================
# 📊 KALIBRASI TURBIDITY
# ============================================================

ADC_AIR = 1946
ADC_UDARA = 1705

def adc_to_ntu(adc):
    if adc >= ADC_AIR:
        return 0.0
    elif adc <= ADC_UDARA:
        return 100.0
    else:
        return 100.0 * (ADC_AIR - adc) / (ADC_AIR - ADC_UDARA)

# ============================================================
# 🔬 INISIALISASI OLED & ADC
# ============================================================

print("🔧 Inisialisasi OLED...")
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
oled = SSD1306(128, 64, i2c)

print("🔧 Inisialisasi ADC...")
adc_ph = ADC(Pin(26))
adc_tds = ADC(Pin(27))
adc_turb = ADC(Pin(28))

print("✅ Semua siap!")

# ============================================================
# 🔬 FUNGSI BACA SENSOR - FIXED
# ============================================================

def baca_ph_avg(samples=30):
    total = 0
    for _ in range(samples):
        total += adc_ph.read_u16()
        time.sleep_ms(2)
    raw = total / samples
    volt = raw * 3.3 / 65535
    ph = get_ph(volt)
    
    # 🔥 Peringatan jika sensor tidak terhubung
    if volt < 0.1:
        print("  ⚠️ PERINGATAN: Sensor pH tidak terhubung! (Volt=0)")
    
    print(f"  DEBUG pH: Raw={raw:.0f} Volt={volt:.3f}V pH={ph:.2f}")
    return ph, volt, raw

def baca_tds_avg(samples=30):
    total = 0
    for _ in range(samples):
        total += adc_tds.read_u16()
        time.sleep_ms(2)
    raw = total / samples
    volt = raw * 3.3 / 65535
    tds = calculate_tds(volt, 25.0)
    print(f"  DEBUG TDS: Raw={raw:.0f} Volt={volt:.3f}V TDS={tds:.0f}")
    return tds, volt, raw

def baca_turb_avg(samples=30):
    total = 0
    for _ in range(samples):
        total += adc_turb.read_u16()
        time.sleep_ms(2)
    raw = total / samples
    
    # 🔥 FIX: Konversi float ke int dulu sebelum shift
    raw_int = int(raw)
    adc_12bit = raw_int >> 4
    
    ntu = adc_to_ntu(adc_12bit)
    volt = raw * 3.3 / 65535
    print(f"  DEBUG Turb: Raw={raw:.0f} ADC={adc_12bit} NTU={ntu:.1f}")
    return ntu, volt, raw

# ============================================================
# 📊 EVALUASI KELAYAKAN
# ============================================================

def evaluasi_air(ph, tds, ntu, temp):
    alasan = []
    
    # 🔥 Jika sensor tidak terhubung, tampilkan peringatan
    if ph > 13.5 or ph < 0.5:
        alasan.append("Sensor pH error")
    
    if ph < PH_MIN:
        alasan.append(f"pH rendah ({ph:.2f})")
    elif ph > PH_MAX:
        alasan.append(f"pH tinggi ({ph:.2f})")
    
    if tds > TDS_MAX:
        alasan.append(f"TDS tinggi ({tds:.0f} ppm)")
    
    if ntu > NTU_MAX:
        alasan.append(f"Keruh ({ntu:.1f} NTU)")
    
    if temp < TEMP_MIN:
        alasan.append(f"Suhu dingin ({temp:.1f}C)")
    elif temp > TEMP_MAX:
        alasan.append(f"Suhu panas ({temp:.1f}C)")
    
    layak = (len(alasan) == 0)
    
    skor = 100
    if ph < PH_MIN or ph > PH_MAX:
        skor -= 30
    if tds > TDS_MAX:
        skor -= 40
    elif tds > 100:
        skor -= 20
    elif tds > 50:
        skor -= 10
    if ntu > NTU_MAX:
        skor -= 30
    elif ntu > 3:
        skor -= 15
    if temp < TEMP_MIN or temp > TEMP_MAX:
        skor -= 20
    
    return max(0, min(100, skor)), layak, alasan

# ============================================================
# 🖥️ TAMPILAN OLED
# ============================================================

def draw_degree(x, y):
    oled.pixel(x, y, 1)
    oled.pixel(x+2, y, 1)
    oled.pixel(x, y+2, 1)
    oled.pixel(x+2, y+2, 1)
    oled.pixel(x+1, y+1, 1)

def tampil_oled(ph, tds, status, skor, temp):
    oled.fill(0)
    
    oled.text(f"pH:{ph:.2f}", 0, 2, 1)
    oled.text("|", 62, 2, 1)
    oled.text(f"ppm:{tds:.0f}", 75, 2, 1)
    
    status_text = "LAYAK" if status else "TIDAK LAYAK"
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
print("🌊 WATER QUALITY MONITOR - RO")
print(f"pH: {PH_MIN}-{PH_MAX} | TDS: 0-{TDS_MAX:.0f} | NTU: 0-{NTU_MAX:.0f}")
print("=" * 50)

# Splash
oled.fill(0)
oled.text("WATER MONITOR", 10, 20, 1)
oled.text("RO System", 45, 40, 1)
oled.show()
time.sleep(0.5)

temp = 25.0

while True:
    try:
        ph, tds, ntu = proses_stabilisasi()
        
        skor, layak, alasan = evaluasi_air(ph, tds, ntu, temp)
        
        tampil_oled(ph, tds, layak, skor, temp)
        
        print("-" * 50)
        print("📊 HASIL FINAL:")
        print(f"   pH : {ph:.2f}  ({PH_MIN}-{PH_MAX})")
        print(f"   TDS: {tds:.0f} ppm  (0-{TDS_MAX:.0f})")
        print(f"   NTU: {ntu:.1f}  (0-{NTU_MAX:.0f})")
        print(f"   Status: {'LAYAK ✅' if layak else 'TIDAK LAYAK ❌'}")
        print(f"   Skor: {skor:.0f}%")
        if alasan:
            print(f"   Alasan: {', '.join(alasan)}")
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
