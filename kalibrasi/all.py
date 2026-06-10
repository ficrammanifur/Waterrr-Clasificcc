# ====================================================================
# WATER QUALITY MONITORING SYSTEM - Raspberry Pi Pico 2
# VERSI DENGAN KOREKSI pH & TDS
# ====================================================================

from machine import ADC, Pin
import dht
import time

# ============ PIN DEFINITIONS ============
PIN_PH = 26
PIN_TDS = 27
PIN_TURBIDITY = 28
PIN_DHT = 20

# ============ INISIALISASI SENSOR ============
ph_sensor = ADC(Pin(PIN_PH))
tds_sensor = ADC(Pin(PIN_TDS))
turb_sensor = ADC(Pin(PIN_TURBIDITY))
dht_sensor = dht.DHT22(Pin(PIN_DHT, Pin.IN, Pin.PULL_UP))

# ============ KALIBRASI pH (KOREKSI BERDASARKAN TESTER) ============
# Data: pH terbaca 8.39, target 8.01, selisih +0.38
# Maka PH_OFFSET baru = PH_OFFSET - 0.38

PH_SLOPE = -7.29
PH_OFFSET = 27.90 - 0.38  # Koreksi: 27.90 - 0.38 = 27.52

# ============ KALIBRASI TDS (PERBAIKI) ============
# Data: TDS tester = 180 ppm pada suhu 30°C
# Ambil rata-rata raw TDS dari data Anda: sekitar 640-650

RAW_TDS_REF = 645        # Raw ADC rata-rata dari data Anda
TDS_REF = 180            # TDS dari tester (ppm)
SUHU_KALIBRASI_TDS = 30.0

# Hitung slope baru
TDS_SLOPE = TDS_REF / RAW_TDS_REF  # = 180 / 645 = 0.279

# ============ KALIBRASI TURBIDITY ============
TURB_JERNIH = 2150
TURB_KERUH = 200
TURB_RANGE = TURB_JERNIH - TURB_KERUH

# ============ KOMPENSASI SUHU ============
SUHU_REFERENSI = 25.0
KOEFISIEN_SUHU_PH = 0.003
KOEFISIEN_SUHU_TDS = 0.02

# ============ STANDAR WHO ============
PH_MIN_LAYAK = 6.5
PH_MAX_LAYAK = 8.5
TDS_MAX_LAYAK = 600
TURB_MAX_LAYAK = 5

# ============ FILTER SETTINGS ============
HISTORY_SIZE = 10
ph_history = []
tds_history = []
turb_history = []

# ============ FUNGSI BACA DHT22 DENGAN RETRY LEBIH BAIK ============
def baca_suhu():
    """Baca suhu dengan retry dan delay yang tepat"""
    for attempt in range(5):
        try:
            dht_sensor.measure()
            suhu = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            if -40 < suhu < 80 and 0 < humidity < 100:
                return suhu, humidity
        except Exception as e:
            if attempt == 0:
                pass  # Jangan print error setiap kali
        time.sleep(0.8)
    return 30.0, 75.0

# ============ FUNGSI BACA pH ============
def baca_raw_ph():
    """Baca raw ADC dengan filter sederhana"""
    samples = []
    for _ in range(20):
        samples.append(ph_sensor.read_u16() >> 4)
        time.sleep_ms(30)
    samples.sort()
    return sum(samples[3:17]) // 14

def baca_ph(suhu):
    raw = baca_raw_ph()
    voltage = raw * 3.3 / 4095.0
    ph_25c = (PH_SLOPE * voltage) + PH_OFFSET
    ph_aktual = ph_25c + (KOEFISIEN_SUHU_PH * (suhu - SUHU_REFERENSI))
    
    if ph_aktual < 0:
        ph_aktual = 0
    elif ph_aktual > 14:
        ph_aktual = 14
    
    return round(ph_aktual, 2), raw, voltage

# ============ FUNGSI BACA TDS ============
def baca_raw_tds():
    samples = []
    for _ in range(20):
        samples.append(tds_sensor.read_u16() >> 4)
        time.sleep_ms(30)
    samples.sort()
    return sum(samples[3:17]) // 14

def baca_tds(suhu):
    raw = baca_raw_tds()
    voltage = raw * 3.3 / 4095.0
    
    # TDS pada suhu kalibrasi
    tds_pada_30c = raw * TDS_SLOPE
    
    # Koreksi ke suhu aktual (2% per °C)
    faktor_koreksi = 1 + KOEFISIEN_SUHU_TDS * (suhu - SUHU_KALIBRASI_TDS)
    tds_aktual = tds_pada_30c * faktor_koreksi
    
    if tds_aktual < 0:
        tds_aktual = 0
    
    return round(tds_aktual), raw, voltage

# ============ FUNGSI BACA TURBIDITY ============
def baca_raw_turb():
    samples = []
    for _ in range(20):
        samples.append(turb_sensor.read_u16() >> 4)
        time.sleep_ms(30)
    samples.sort()
    return sum(samples[3:17]) // 14

def baca_turbidity():
    raw = baca_raw_turb()
    voltage = raw * 3.3 / 4095.0
    
    if raw >= TURB_JERNIH:
        ntu = 0.0
    elif raw <= TURB_KERUH:
        ntu = 100.0
    else:
        ntu = (TURB_JERNIH - raw) * 100.0 / TURB_RANGE
    
    if ntu < 0:
        ntu = 0
    elif ntu > 100:
        ntu = 100
    
    return round(ntu, 1), raw, voltage

# ============ STATUS ============
def status_ph(ph):
    if ph < 6.5:
        return "ASAM"
    elif ph > 8.5:
        return "BASA"
    return "NETRAL"

def status_tds(tds):
    if tds <= 50:
        return "SANGAT TAWAR"
    elif tds <= 300:
        return "AIR TAWAR"
    elif tds <= 600:
        return "LAYAK MINUM"
    elif tds <= 1000:
        return "AGAK ASIN"
    return "ASIN"

def status_turb(ntu):
    if ntu <= 1:
        return "SANGAT JERNIH"
    elif ntu <= 5:
        return "JERNIH"
    elif ntu <= 20:
        return "AGAK KERUH"
    elif ntu <= 50:
        return "KERUH"
    return "SANGAT KERUH"

def kelayakan(ph, tds, ntu):
    ph_ok = PH_MIN_LAYAK <= ph <= PH_MAX_LAYAK
    tds_ok = tds <= TDS_MAX_LAYAK
    turb_ok = ntu <= TURB_MAX_LAYAK
    
    if ph_ok and tds_ok and turb_ok:
        return "LAYAK ✅"
    
    masalah = []
    if not ph_ok:
        masalah.append(f"pH={ph}")
    if not tds_ok:
        masalah.append(f"TDS={tds}")
    if not turb_ok:
        masalah.append(f"NTU={ntu}")
    return f"TIDAK LAYAK ❌ ({', '.join(masalah)})"

# ============ PROGRAM UTAMA ============
print("\n" + "="*80)
print("   WATER QUALITY MONITORING SYSTEM (KOREKSI)")
print("="*80)

# Cek DHT22
print("\n🔍 Mengecek sensor DHT22...")
for i in range(3):
    try:
        dht_sensor.measure()
        suhu_test = dht_sensor.temperature()
        hum_test = dht_sensor.humidity()
        print(f"✅ DHT22 OK! Suhu: {suhu_test:.1f}°C, RH: {hum_test:.1f}%")
        break
    except:
        print(f"   Percobaan {i+1} gagal...")
        time.sleep(1)

print("\n🔍 Stabilisasi sensor (5 detik)...")
for i in range(5):
    print(f"   {5-i} detik...")
    time.sleep(1)

print("\n" + "-"*80)
print(f"{'pH':>8} | {'TDS':>6} | {'NTU':>6} | {'Suhu':>6} | {'RH':>5} | {'Status Air':>30} | {'Kelayakan':>25}")
print("-"*80)

# Moving average buffers
ph_ma = []
tds_ma = []
turb_ma = []

while True:
    try:
        suhu, humidity = baca_suhu()
        ph, ph_raw, ph_volt = baca_ph(suhu)
        tds, tds_raw, tds_volt = baca_tds(suhu)
        ntu, turb_raw, turb_volt = baca_turbidity()
        
        # Moving average
        ph_ma.append(ph)
        tds_ma.append(tds)
        turb_ma.append(ntu)
        
        if len(ph_ma) > 10:
            ph_ma.pop(0)
            tds_ma.pop(0)
            turb_ma.pop(0)
        
        ph_stabil = sum(ph_ma) / len(ph_ma)
        tds_stabil = sum(tds_ma) / len(tds_ma)
        ntu_stabil = sum(turb_ma) / len(turb_ma)
        
        status_str = f"{status_ph(ph_stabil)} | {status_tds(tds_stabil)} | {status_turb(ntu_stabil)}"
        layak = kelayakan(ph_stabil, tds_stabil, ntu_stabil)
        
        print(f"{ph_stabil:8.2f} | {tds_stabil:6.0f} | {ntu_stabil:6.1f} | {suhu:6.1f}°C | {humidity:5.0f}% | {status_str:>30} | {layak:>25}")
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n" + "-"*80)
        print("\n📊 Program selesai")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)
