"""
Water Quality Monitor - Pico 2 FINAL
TDS: R² = 0.9998, MAE = 23.65 ppm
pH: Kalibrasi dari data real (100 sample average)
pH = -14.26 × Volt + 22.02
"""

import time
import math
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306

# ============================================================
# 📊 PARAMETER TDS DARI COLAB
# ============================================================

TDS_COEF = [1726.481171, -3.070768]
TDS_INTERCEPT = 232.465278
TDS_SCALER_MEAN = [0.562986, 29.247326]
TDS_SCALER_SCALE = [0.147120, 0.151871]

# ============================================================
# 📊 KALIBRASI pH - DARI DATA REAL (100 SAMPLE AVERAGE)
# ============================================================

# pH = -14.26 × Volt + 22.02
PH_SLOPE = -14.26
PH_INTERCEPT = 22.02

def get_ph(volt):
    """Hitung pH dari voltase"""
    ph = PH_SLOPE * volt + PH_INTERCEPT
    return max(0, min(14, ph))

def baca_ph_avg(samples=100):
    """Baca pH dengan rata-rata 100 sampel"""
    adc_ph = ADC(Pin(26))
    total = 0
    for _ in range(samples):
        total += adc_ph.read_u16()
        time.sleep_ms(5)
    
    raw = total / samples
    volt = raw * 3.3 / 65535
    ph = get_ph(volt)
    return ph, volt, raw

# ============================================================
# 🔬 FUNGSI PREDIKSI TDS
# ============================================================

def predict_tds(tds_volt, suhu):
    z0 = (tds_volt - TDS_SCALER_MEAN[0]) / TDS_SCALER_SCALE[0]
    z1 = (suhu - TDS_SCALER_MEAN[1]) / TDS_SCALER_SCALE[1]
    tds = TDS_INTERCEPT + TDS_COEF[0] * z0 + TDS_COEF[1] * z1
    return max(0, tds)

def baca_tds_avg(samples=100):
    """Baca TDS dengan rata-rata 100 sampel"""
    adc_tds = ADC(Pin(27))
    total = 0
    for _ in range(samples):
        total += adc_tds.read_u16()
        time.sleep_ms(5)
    
    raw = total / samples
    volt = raw * 3.3 / 65535
    tds = predict_tds(volt, 25.0)
    return tds, volt, raw

# ============================================================
# 🖥️ TAMPILAN OLED
# ============================================================

def draw_degree(x, y):
    oled.pixel(x, y, 1)
    oled.pixel(x+2, y, 1)
    oled.pixel(x, y+2, 1)
    oled.pixel(x+2, y+2, 1)
    oled.pixel(x+1, y+1, 1)

def tampil_oled(ph, tds, status, skor, suhu):
    oled.fill(0)
    
    oled.text(f"pH:{ph:.2f}", 0, 2, 1)
    oled.text("|", 62, 2, 1)
    oled.text(f"ppm:{tds:.0f}", 75, 2, 1)
    
    status_text = "LAYAK" if status else "TIDAK LAYAK"
    x = (128 - len(status_text) * 8) // 2
    oled.text(status_text, x, 20, 1)
    
    oled.hline(0, 36, 128, 1)
    
    oled.text(f"{skor:.0f}%", 0, 50, 1)
    
    suhu_str = f"{suhu:.1f}"
    suhu_x = 128 - 44
    oled.text(suhu_str, suhu_x, 50, 1)
    degree_x = suhu_x + (len(suhu_str) * 8)
    draw_degree(degree_x, 48)
    oled.text("C", degree_x + 3, 50, 1)
    
    oled.show()

# ============================================================
# 📊 EVALUASI KELAYAKAN
# ============================================================

def evaluasi_air(ph, tds):
    alasan = []
    
    if ph < 6.5:
        alasan.append(f"pH rendah ({ph:.2f})")
    elif ph > 8.5:
        alasan.append(f"pH tinggi ({ph:.2f})")
    
    if tds > 500:
        alasan.append(f"TDS tinggi ({tds:.0f} ppm)")
    elif tds > 300:
        alasan.append(f"TDS cukup tinggi ({tds:.0f} ppm)")
    
    layak = (len(alasan) == 0)
    
    skor = 100
    if ph < 6.5 or ph > 8.5:
        skor -= 30
    if tds > 500:
        skor -= 40
    elif tds > 300:
        skor -= 20
    elif tds > 200:
        skor -= 10
    
    return max(0, min(100, skor)), layak, alasan

# ============================================================
# 🕐 STABILISASI 15 DETIK
# ============================================================

STABIL_DURASI = 15

def proses_stabilisasi():
    print(f"\n⏳ Stabilisasi {STABIL_DURASI} detik...")
    print("=" * 60)
    print("  Waktu  |   pH   |  pH Volt |  TDS  | TDS Volt")
    print("=" * 60)
    
    ph_list = []
    tds_list = []
    
    for i in range(STABIL_DURASI):
        ph, ph_volt, _ = baca_ph_avg(50)
        tds, tds_volt, _ = baca_tds_avg(50)
        
        ph_list.append(ph)
        tds_list.append(tds)
        
        if i % 3 == 0:
            sisa = STABIL_DURASI - i
            ph_avg = sum(ph_list) / len(ph_list)
            tds_avg = sum(tds_list) / len(tds_list)
            print(f"  t-{sisa:2d}s | {ph_avg:6.2f} |  {ph_volt:.3f}V  | {tds_avg:5.0f} |   {tds_volt:.3f}V")
        
        time.sleep(0.3)
    
    ph_akhir = sum(ph_list) / len(ph_list)
    tds_akhir = sum(tds_list) / len(tds_list)
    
    print("=" * 60)
    print(f"\n✅ Selesai! pH={ph_akhir:.2f}, TDS={tds_akhir:.0f} ppm")
    return ph_akhir, tds_akhir

# ============================================================
# 🚀 MAIN PROGRAM
# ============================================================

print("=" * 50)
print("🌊 WATER QUALITY MONITOR")
print(f"TDS: R² = 0.9998, MAE = 23.65 ppm")
print("pH: Kalibrasi 100 sample average")
print(f"   pH = {PH_SLOPE:.2f} × Volt + {PH_INTERCEPT:.2f}")
print("=" * 50)

# Inisialisasi OLED
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
oled = SSD1306(128, 64, i2c)

# Splash
oled.fill(0)
oled.text("WATER MONITOR", 10, 20, 1)
oled.text("v2.0", 55, 40, 1)
oled.show()
time.sleep(0.8)

suhu = 25.0

while True:
    try:
        ph, tds = proses_stabilisasi()
        
        skor, layak, alasan = evaluasi_air(ph, tds)
        
        tampil_oled(ph, tds, layak, skor, suhu)
        
        print("-" * 50)
        print("📊 HASIL FINAL:")
        print(f"   pH : {ph:.2f}")
        print(f"   TDS: {tds:.0f} ppm")
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
