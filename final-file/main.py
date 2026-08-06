"""
Water Quality Monitor - Simple Version
Raspberry Pi Pico 2 (RP2350)
pH: 3-Titik Kalibrasi | TDS: Rata-rata 3 terdekat
"""

import time
import onewire
import ds18x20
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306
from calibration import get_ph, get_tds

# ============================================================
# KONFIGURASI HARDWARE
# ============================================================

i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
oled = SSD1306(128, 64, i2c)

adc_ph = ADC(Pin(26))
adc_tds = ADC(Pin(27))
adc_turb = ADC(Pin(28))

# DS18B20
ow = onewire.OneWire(Pin(16))
ds = ds18x20.DS18X20(ow)
roms = ds.scan()

if len(roms) == 0:
    ds_ok = False
else:
    ds_ok = True

led = Pin(25, Pin.OUT)

# ============================================================
# FUNGSI BACA SENSOR
# ============================================================

def baca_ph():
    adc_list = []
    for _ in range(10):
        adc_list.append(adc_ph.read_u16())
        time.sleep_ms(5)
    
    adc_list.sort()
    raw = adc_list[len(adc_list) // 2]
    volt = raw * 3.3 / 65535
    ph = get_ph(volt)
    return ph, volt, raw

def baca_tds():
    adc_list = []
    for _ in range(10):
        adc_list.append(adc_tds.read_u16())
        time.sleep_ms(5)
    
    raw = sum(adc_list) // len(adc_list)
    volt = raw * 3.3 / 65535
    tds = get_tds(volt)
    return tds, volt, raw

def baca_turbidity():
    raw = adc_turb.read_u16() >> 4
    if raw >= 2048:
        return 0.0
    elif raw <= 80:
        return 100.0
    else:
        return max(0, min(100, (2048 - raw) * 100 / (2048 - 80)))

def baca_suhu():
    if not ds_ok:
        return 25.0
    try:
        ds.convert_temp()
        time.sleep_ms(750)
        return ds.read_temp(roms[0])
    except:
        return 25.0

# ============================================================
# TAMPILAN OLED
# ============================================================

def tampil_hasil(ph, tds, layak, skor, temp):
    oled.fill(0)
    
    oled.text(f"pH:{ph:.2f}", 0, 2, 1)
    oled.text("|", 62, 2, 1)
    oled.text(f"ppm:{tds:.0f}", 75, 2, 1)
    
    status = "LAYAK" if layak else "TIDAK LAYAK"
    x = (128 - len(status) * 8) // 2
    oled.text(status, x, 20, 1)
    
    oled.hline(0, 40, 128, 1)
    
    oled.text(f"{skor:.0f}%", 0, 52, 1)
    oled.text(f"{temp:.1f}C", 85, 52, 1)
    
    oled.show()

# ============================================================
# EVALUASI
# ============================================================

def evaluasi(ph, tds, ntu):
    alasan = []
    
    if tds > 500:
        alasan.append(f"TDS {tds:.0f}")
    if ntu > 5:
        alasan.append(f"Keruh {ntu:.1f}")
    if ph < 6.5 or ph > 9.8:
        alasan.append(f"pH {ph:.2f}")
    
    layak = (len(alasan) == 0)
    skor = max(0, 100 - (len(alasan) * 25))
    
    return layak, skor, alasan

# ============================================================
# PROGRAM UTAMA
# ============================================================

print("=" * 40)
print("🌊 WATER QUALITY MONITOR")
print("pH: 3-Titik Kalibrasi")
print("TDS: Rata-rata 3 terdekat")
print("=" * 40)

oled.fill(0)
oled.text("WATER MONITOR", 15, 20, 1)
oled.text("v1.0", 55, 40, 1)
oled.show()
time.sleep(0.8)

try:
    print("\n⏳ Membaca sensor (20x)...")
    
    ph_list = []
    tds_list = []
    ntu_list = []
    
    for i in range(20):
        ph, ph_volt, ph_raw = baca_ph()
        tds, tds_volt, tds_raw = baca_tds()
        ntu = baca_turbidity()
        
        ph_list.append(ph)
        tds_list.append(tds)
        ntu_list.append(ntu)
        
        oled.fill(0)
        oled.text("Membaca...", 25, 20, 1)
        oled.text(f"{i+1}/20", 55, 40, 1)
        oled.text(f"pH:{ph:.2f}", 5, 55, 1)
        oled.text(f"TDS:{tds:.0f}", 75, 55, 1)
        oled.show()
        
        print(f"  pH={ph:.2f} ({ph_volt:.3f}V) | TDS={tds:.0f} ({tds_volt:.3f}V) | NTU={ntu:.1f}")
        
        time.sleep(0.5)
    
    ph_akhir = sum(ph_list) / len(ph_list)
    tds_akhir = sum(tds_list) / len(tds_list)
    ntu_akhir = sum(ntu_list) / len(ntu_list)
    suhu = baca_suhu()
    
    layak, skor, alasan = evaluasi(ph_akhir, tds_akhir, ntu_akhir)
    
    print("\n" + "=" * 40)
    print("📊 HASIL:")
    print(f"   pH : {ph_akhir:.2f}")
    print(f"   TDS: {tds_akhir:.0f} ppm")
    print(f"   NTU: {ntu_akhir:.1f}")
    print(f"   Suhu: {suhu:.2f}C")
    print(f"   Status: {'LAYAK ✅' if layak else 'TIDAK LAYAK ❌'}")
    if alasan:
        print(f"   Alasan: {', '.join(alasan)}")
    print("=" * 40)
    
    tampil_hasil(ph_akhir, tds_akhir, layak, skor, suhu)
    
    print("\n✅ Selesai! Hasil di OLED.")
    print("Tekan RESET untuk baca ulang.\n")
    
    led.off()
    
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n🔴 Berhenti")
except Exception as e:
    print(f"❌ Error: {e}")
    oled.fill(0)
    oled.text("ERROR!", 40, 25, 1)
    oled.text(str(e)[:14], 25, 40, 1)
    oled.show()
