# TDS Meter - Kalibrasi Langsung dengan Tester
from machine import ADC, Pin
import dht
import time

PIN_TDS = 27
PIN_DHT = 20

tds_sensor = ADC(Pin(PIN_TDS))
dht_sensor = dht.DHT22(Pin(PIN_DHT, Pin.IN, Pin.PULL_UP))

# ============ KALIBRASI INTERAKTIF ============
print("\n" + "="*50)
print("   KALIBRASI TDS (1 Titik)")
print("="*50)
print("\n📌 Celupkan sensor ke air yang sudah diketahui TDS-nya")
print("   (gunakan tester TDS reference)")

input("\n⚠️  Tekan Enter setelah sensor stabil di dalam air...")

# Baca raw
samples = []
for _ in range(30):
    samples.append(tds_sensor.read_u16() >> 4)
    time.sleep_ms(50)
samples.sort()
raw = sum(samples[5:25]) // 20

# Baca suhu
for _ in range(3):
    try:
        dht_sensor.measure()
        suhu = dht_sensor.temperature()
        break
    except:
        suhu = 25.0
        time.sleep(0.5)

# Input TDS dari tester
tds_tester = float(input("\n📊 Masukkan TDS dari tester (ppm): "))

# Hitung koreksi
SUHU_REF = 25.0
KOEF = 0.02
tds_25c = tds_tester / (1 + KOEF * (suhu - SUHU_REF))
SLOPE = tds_25c / raw

print("\n" + "="*50)
print("   HASIL KALIBRASI")
print("="*50)
print(f"Raw ADC: {raw}")
print(f"Suhu: {suhu:.1f}°C")
print(f"TDS tester: {tds_tester} ppm")
print(f"TDS terkoreksi ke 25°C: {tds_25c:.1f} ppm")
print(f"\nRumus: TDS = {SLOPE:.6f} x Raw")
print("="*50)

# Mulai pembacaan
print("\n✅ Mulai membaca TDS...\n")
print("-"*60)

history = []
while True:
    try:
        raw = tds_sensor.read_u16() >> 4
        
        # Baca suhu
        try:
            dht_sensor.measure()
            suhu = dht_sensor.temperature()
        except:
            suhu = 25.0
        
        tds_25c = SLOPE * raw
        tds_aktual = tds_25c * (1 + KOEF * (suhu - SUHU_REF))
        
        history.append(tds_aktual)
        if len(history) > 10:
            history.pop(0)
        tds_tampil = sum(history) / len(history)
        
        print(f"Raw: {raw:4.0f} | Suhu: {suhu:5.1f}°C | TDS: {tds_tampil:5.0f} ppm")
        time.sleep(2)
        
    except KeyboardInterrupt:
        break
