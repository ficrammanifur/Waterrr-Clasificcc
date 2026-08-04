"""
Water Quality Monitor - ML Edition
Raspberry Pi Pico 2 (RP2350)
Single Read - Tampilan Final
"""

import time
import math
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306

# ============================================================
# KONFIGURASI HARDWARE
# ============================================================

i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
oled = SSD1306(128, 64, i2c)

adc_ph = ADC(Pin(26))
adc_tds = ADC(Pin(27))
adc_turb = ADC(Pin(28))

led = Pin(25, Pin.OUT)

# ============================================================
# 📊 KALIBRASI pH - 3 POINT
# ============================================================

V4, PH4 = 3.290, 4.00
V7, PH7 = 2.870, 6.86
V9, PH9 = 2.522, 9.18

def get_ph(voltage):
    if voltage >= V7:
        return PH4 + (PH7 - PH4) * (V4 - voltage) / (V4 - V7)
    else:
        return PH7 + (PH9 - PH7) * (V7 - voltage) / (V7 - V9)

# ============================================================
# 📊 KALIBRASI TDS
# ============================================================

TDS_A1 = -84457.6393026635
TDS_A2 = 129089.75684172624
TDS_A3 = -64637.674455130655
TDS_B = 18201.754358930462

def voltage_to_tds(voltage):
    tds = (TDS_A1 * voltage +
           TDS_A2 * (voltage ** 2) +
           TDS_A3 * (voltage ** 3) +
           TDS_B)
    return max(0, tds)

# ============================================================
# 📊 KALIBRASI TURBIDITY
# ============================================================

TURB_JERNIH = 2048
TURB_KERUH = 80
TURB_RANGE = TURB_JERNIH - TURB_KERUH

def adc_to_ntu(adc):
    if adc >= TURB_JERNIH:
        return 0.0
    elif adc <= TURB_KERUH:
        return 100.0
    else:
        return max(0, min(100, (TURB_JERNIH - adc) * 100.0 / TURB_RANGE))

def ntu_to_persen_jernih(ntu):
    return max(0, min(100, 100 - ntu))

# ============================================================
# 🤖 LOGISTIC REGRESSION
# ============================================================

PH_CENTER = 7.15
SCALER_MEAN = [7.511250, 3.573763, 270.678571]
SCALER_SCALE = [1.855603, 6.555135, 503.141208]
COEF = [2.158634, -0.495534, -1.689377]
INTERCEPT = -0.153053

def sigmoid(x):
    if x < -30:
        return 0.0
    if x > 30:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))

def predict_ph_tds_layak(ph, tds):
    feat = [ph, (ph - PH_CENTER) ** 2, tds]
    z = [(feat[i] - SCALER_MEAN[i]) / SCALER_SCALE[i] for i in range(3)]
    logit = INTERCEPT
    for i in range(3):
        logit += COEF[i] * z[i]
    prob = sigmoid(logit)
    return prob >= 0.5, prob

# ============================================================
# 📊 EVALUASI
# ============================================================

TDS_HARD_MAX = 500.0
NTU_MAX = 5.0

def evaluasi_air(ph, tds, ntu):
    alasan = []
    
    if tds > TDS_HARD_MAX:
        alasan.append("TDS tinggi")
    if ntu > NTU_MAX:
        alasan.append("Keruh")
    
    model_layak, prob = predict_ph_tds_layak(ph, tds)
    if not model_layak:
        alasan.append("pH/TDS tidak sehat")
    
    is_layak = (len(alasan) == 0)
    
    skor = prob * 100
    if tds > TDS_HARD_MAX:
        skor = min(skor, 20)
    if ntu > NTU_MAX:
        skor = min(skor, 30)
    
    return is_layak, skor, alasan

# ============================================================
# 🎬 TAMPILAN
# ============================================================

def splash_screen():
    oled.fill(0)
    oled.text("WATER MONITOR", 15, 20, 1)
    oled.text("v1.0", 55, 40, 1)
    oled.show()
    time.sleep(0.8)

def tampil_stabilisasi(detik):
    oled.fill(0)
    oled.text("Membaca...", 25, 20, 1)
    oled.text(f"{detik}s", 55, 40, 1)
    oled.show()

def tampil_hasil(ph, tds, layak, skor, temp):
    oled.fill(0)
    
    # === BARIS 1: pH | ppm ===
    oled.text(f"pH:{ph:.2f}", 0, 2, 1)          # kiri
    oled.text("|", 62, 2, 1)                    # garis pemisah
    oled.text(f"ppm:{tds:.0f}", 70, 2, 1)       # kanan
    
    # === BARIS 2 + 3: STATUS (tengah, 2 baris) ===
    status = "LAYAK" if layak else "TIDAK LAYAK"
    x = (128 - len(status) * 8) // 2
    oled.text(status, x, 20, 1)                 # baris 2
    
    # === BARIS 3: KOSONG (spasi) ===
    # (biar status lebih lega)
    
    # === BARIS 4: GARIS BAWAH STATUS ===
    oled.hline(0, 40, 128, 1)
    
    # === BARIS 5: Skor (kiri) | Suhu (kanan) - TANPA garis ===
    oled.text(f"{skor:.0f}%", 0, 52, 1)          # kiri
    oled.text(f"{temp:.1f}C", 85, 52, 1)         # kanan
    
    oled.show()

# ============================================================
# 🕐 STABILISASI 60 DETIK
# ============================================================

def proses_stabilisasi():
    ph_filtered = 7.0
    EMA_ALPHA = 0.15
    tds_peak_voltage = 0.0
    turb_samples = []
    
    print("\n⏳ Stabilisasi 60 detik...")
    
    for i in range(60):
        # pH
        ph_raw_adc = adc_ph.read_u16()
        ph_volt = ph_raw_adc / 65535 * 3.3
        ph_instant = get_ph(ph_volt)
        ph_filtered = (1 - EMA_ALPHA) * ph_filtered + EMA_ALPHA * ph_instant
        ph_filtered = max(0, min(14, ph_filtered))
        
        # TDS - Peak Hold
        tds_raw_adc = adc_tds.read_u16()
        tds_volt = tds_raw_adc / 65535 * 3.3
        if tds_volt > tds_peak_voltage:
            tds_peak_voltage = tds_volt
        
        # Turbidity
        turb_raw = adc_turb.read_u16() >> 4
        turb_samples.append(turb_raw)
        
        led.toggle()
        
        # Tampilkan setiap 5 detik
        if i % 5 == 0:
            sisa = 60 - i
            tampil_stabilisasi(sisa)
            print(f"  t-{sisa}s | pH={ph_filtered:.2f}")
        
        time.sleep(0.3)
    
    led.off()
    
    # Hasil akhir
    turb_avg_adc = sum(turb_samples) / len(turb_samples)
    ntu = adc_to_ntu(turb_avg_adc)
    tds_final = voltage_to_tds(tds_peak_voltage)
    
    print(f"\n✅ Selesai! pH={ph_filtered:.2f} TDS={tds_final:.0f} NTU={ntu:.1f}")
    
    return ph_filtered, tds_final, ntu

# ============================================================
# PROGRAM UTAMA
# ============================================================

print("=" * 40)
print("🌊 WATER QUALITY MONITOR")
print("Single Read Mode")
print("=" * 40)

splash_screen()

temperature = 25.0

try:
    ph, tds, ntu = proses_stabilisasi()
    
    layak, skor, alasan = evaluasi_air(ph, tds, ntu)
    
    persen_jernih = ntu_to_persen_jernih(ntu)
    skor_akhir = (skor + persen_jernih) / 2
    
    print("-" * 40)
    print("📊 HASIL:")
    print(f"pH: {ph:.2f}  |  TDS: {tds:.0f} ppm")
    print(f"NTU: {ntu:.1f}  |  Jernih: {persen_jernih:.0f}%")
    print(f"Status: {'LAYAK ✅' if layak else 'TIDAK LAYAK ❌'}")
    if alasan:
        print(f"Alasan: {', '.join(alasan)}")
    print("-" * 40)
    
    # TAMPILAN HASIL
    tampil_hasil(ph, tds, layak, skor_akhir, temperature)
    
    print("\n✅ Selesai! Hasil ditampilkan di OLED.")
    print("Tekan RESET untuk baca ulang.\n")
    
    # LED mati
    led.off()
    
    # Loop forever - hanya menampilkan hasil di OLED
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
