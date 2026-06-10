# pH Meter dengan Kalibrasi 8 Titik (Dari Semua Data Tester)
# GPIO 26 = pH Sensor, GPIO 20 = DHT22

from machine import ADC, Pin
import dht
import time

# ============ PIN DEFINITIONS ============
PIN_PH = 26
PIN_DHT = 20

# ============ INISIALISASI SENSOR ============
ph_sensor = ADC(Pin(PIN_PH))
dht_sensor = dht.DHT22(Pin(PIN_DHT, Pin.IN, Pin.PULL_UP))

# ============ KALIBRASI pH (8 TITIK DARI DATA TESTER) ============
# Hasil regresi linear dari 8 titik:
# Slope = -7.29
# Intercept = 27.90

PH_SLOPE = -7.29
PH_OFFSET = 27.90

# ============ KOMPENSASI SUHU ============
SUHU_REFERENSI = 25.0
KOEFISIEN_SUHU_PH = 0.003

# ============ FUNGSI BACA ============
def baca_suhu():
    for attempt in range(3):
        try:
            dht_sensor.measure()
            suhu = dht_sensor.temperature()
            if -40 < suhu < 80:
                return suhu, dht_sensor.humidity()
        except:
            pass
        time.sleep(0.5)
    return 30.0, 75.0

def baca_raw_ph_stabil(samples=30):
    raw_samples = []
    for _ in range(samples):
        raw_samples.append(ph_sensor.read_u16() >> 4)
        time.sleep_ms(40)
    raw_samples.sort()
    start = int(len(raw_samples) * 0.2)
    end = int(len(raw_samples) * 0.8)
    filtered = raw_samples[start:end]
    return sum(filtered) // len(filtered)

def baca_ph():
    raw = baca_raw_ph_stabil()
    voltage = raw * 3.3 / 4095.0
    suhu, humidity = baca_suhu()
    
    pH_25c = (PH_SLOPE * voltage) + PH_OFFSET
    pH_aktual = pH_25c + (KOEFISIEN_SUHU_PH * (suhu - SUHU_REFERENSI))
    
    if pH_aktual < 0:
        pH_aktual = 0
    elif pH_aktual > 14:
        pH_aktual = 14
    
    return raw, voltage, round(pH_25c, 2), round(pH_aktual, 2), suhu, humidity

# ============ PROGRAM UTAMA ============
print("\n" + "="*60)
print("   pH METER (8 TITIK) dengan DHT22")
print("="*60)
print(f"Rumus: pH = ({PH_SLOPE} x Voltage) + {PH_OFFSET}")
print("="*60)

# Test DHT22
print("\n🔍 Mengecek DHT22...")
for i in range(3):
    try:
        dht_sensor.measure()
        suhu = dht_sensor.temperature()
        hum = dht_sensor.humidity()
        print(f"✅ DHT22 OK! Suhu: {suhu:.1f}°C, RH: {hum:.1f}%")
        break
    except:
        print(f"   Percobaan {i+1} gagal...")
        time.sleep(1)

print("\n✅ Mulai membaca pH...\n")
print("-"*70)
print(f"{'Raw ADC':>8} | {'Voltage':>8} | {'Suhu':>6} | {'pH_25°C':>8} | {'pH':>8} | {'Status':>12}")
print("-"*70)

history = []
HISTORY_SIZE = 10

while True:
    try:
        raw, voltage, pH_25c, pH_aktual, suhu, humidity = baca_ph()
        
        history.append(pH_aktual)
        if len(history) > HISTORY_SIZE:
            history.pop(0)
        pH_stabil = sum(history) / len(history)
        
        # Status
        if pH_stabil < 6.5:
            status = "ASAM"
        elif pH_stabil > 8.5:
            status = "BASA"
        else:
            status = "NETRAL"
        
        print(f"{raw:8.0f} | {voltage:8.3f}V | {suhu:5.1f}°C | {pH_25c:8.2f} | {pH_stabil:8.2f} | {status:>12}")
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n" + "-"*70)
        break
