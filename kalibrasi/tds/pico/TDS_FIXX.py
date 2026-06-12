# ====================================================================
# TDS METER - AKURAT dengan Tester 263 ppm
# ====================================================================

from machine import ADC, Pin
import time

tds_sensor = ADC(Pin(27))

# ============ KALIBRASI DARI DATA TESTER ============
# Raw ~13300 → TDS 263 ppm (bukan 400 ppm)
# Faktor koreksi = 263 / 400 = 0.6575

TDS_SLOPE = 0.1417      # 0.215505 × 0.6575
TDS_INTERCEPT = -1616.5  # -2458.36 × 0.6575

# Buffer untuk moving average
raw_history = []
MAX_HISTORY = 20

def baca_raw_stabil():
    """Baca raw value dengan filter outlier"""
    # Buang 5 pembacaan pertama
    for _ in range(5):
        tds_sensor.read_u16()
        time.sleep_ms(10)
    
    # Kumpulkan sample
    samples = []
    for _ in range(50):
        samples.append(tds_sensor.read_u16())
        time.sleep_ms(5)
    
    # Filter outlier: buang 20% terendah & 20% tertinggi
    samples.sort()
    start = int(len(samples) * 0.2)
    end = int(len(samples) * 0.8)
    filtered = samples[start:end]
    
    return sum(filtered) / len(filtered)

def baca_tds():
    """Baca TDS akurat sesuai tester"""
    raw = baca_raw_stabil()
    
    # Moving average
    raw_history.append(raw)
    if len(raw_history) > MAX_HISTORY:
        raw_history.pop(0)
    
    raw_avg = sum(raw_history) / len(raw_history)
    
    # Konversi ke ppm dengan rumus terkoreksi
    ppm = TDS_SLOPE * raw_avg + TDS_INTERCEPT
    
    if ppm < 0:
        ppm = 0
    
    volt = raw_avg * 3.3 / 65535.0
    
    return round(ppm, 0), volt, raw_avg

# ============ PROGRAM UTAMA ============
print("\n" + "="*50)
print("   TDS METER - AKURAT")
print("   Kalibrasi dengan tester 263 ppm")
print("="*50)
print(f"Rumus: PPM = {TDS_SLOPE:.4f} × Raw + {TDS_INTERCEPT:.1f}")
print("="*50)

print("\n🔍 Stabilisasi sensor...")
for i in range(5):
    print(f"   {5-i} detik...")
    time.sleep(1)

print("\n✅ Mulai membaca TDS...\n")
print("-"*40)
print(f"{'Raw':>8} | {'Volt':>6} | {'TDS(ppm)':>8}")
print("-"*40)

while True:
    try:
        ppm, volt, raw = baca_tds()
        print(f"{raw:8.0f} | {volt:6.3f}V | {ppm:8.0f}")
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n" + "-"*40)
        print("\n📊 Program selesai")
        break
