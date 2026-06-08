# TDS paling akurat dengan filter
from machine import ADC, Pin
import time
import math

tds_sensor = ADC(Pin(27))

# ============================================
# KALIBRASI DARI DATA ANDA
# ============================================
TDS_SLOPE = 0.215505
TDS_INTERCEPT = -2458.36

# Buffer untuk moving average
raw_history = []
MAX_HISTORY = 30

def baca_raw_stabil():
    """Baca raw value dengan stabilisasi waktu"""
    # Buang 10 pembacaan pertama (sensor masih stabilisasi)
    for _ in range(10):
        tds_sensor.read_u16()
        time.sleep_ms(10)
    
    # Kumpulkan sample
    samples = []
    for _ in range(100):
        samples.append(tds_sensor.read_u16())
        time.sleep_ms(5)
    
    # Urutkan untuk mencari median (buang outlier)
    samples.sort()
    
    # Ambil 60% tengah (buang 20% terendah dan 20% tertinggi)
    start = int(len(samples) * 0.2)
    end = int(len(samples) * 0.8)
    filtered = samples[start:end]
    
    # Rata-rata dari sample yang sudah difilter
    avg_raw = sum(filtered) / len(filtered)
    
    return avg_raw

def baca_tds_akurat():
    """Baca TDS dengan moving average dan filter outlier"""
    raw = baca_raw_stabil()
    
    # Moving average
    raw_history.append(raw)
    if len(raw_history) > MAX_HISTORY:
        raw_history.pop(0)
    
    raw_avg = sum(raw_history) / len(raw_history)
    
    # Konversi ke ppm
    ppm = TDS_SLOPE * raw_avg + TDS_INTERCEPT
    
    if ppm < 0:
        ppm = 0
    
    volt = raw_avg * 3.3 / 65535.0
    
    return round(ppm, 0), volt, raw_avg, raw

# ============================================
# PROGRAM UTAMA
# ============================================
print("\n" + "="*50)
print("   TDS METER ULTIMATE")
print("   Dengan Filter Outlier & Moving Average")
print("="*50)
print(f"Rumus: PPM = {TDS_SLOPE:.6f} × Raw + {TDS_INTERCEPT:.2f}")
print(f"Moving average: {MAX_HISTORY} sampel")
print("="*50)

print("\n🔍 Memulai pembacaan...")
print("   Tunggu 10 detik pertama untuk stabilisasi")
print("   Tekan Ctrl+C untuk berhenti\n")

# Stabilisasi awal
print("Stabilisasi sensor...")
for i in range(10):
    print(f"   {10-i} detik...")
    time.sleep(1)

print("\n✅ Sensor stabil! Mulai membaca...\n")

while True:
    try:
        ppm, volt, raw_avg, raw_last = baca_tds_akurat()
        
        # Tampilkan dengan indikator stabilitas
        if len(raw_history) >= MAX_HISTORY:
            stability = "✅ Stabil"
        else:
            stability = "⏳ Memuat..."
        
        print(f"Raw: {raw_avg:5.0f} | Volt: {volt:.3f}V | TDS: {ppm:4.0f} ppm | {stability}")
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nSelesai")
        break
