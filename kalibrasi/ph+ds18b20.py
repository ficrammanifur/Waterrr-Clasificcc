# ====================================================================
# WATER QUALITY MONITORING - FINAL FIXED VERSION
# Dengan koreksi offset dari hasil verifikasi
# ====================================================================

from machine import ADC, Pin
import onewire, ds18x20
import time

# ============ PIN DEFINITIONS ============
PIN_PH = 26
PIN_TDS = 27
PIN_TURBIDITY = 28
PIN_DS18B20 = 16

# ============ INISIALISASI SENSOR ============
ph_sensor = ADC(Pin(PIN_PH))
tds_sensor = ADC(Pin(PIN_TDS))
turb_sensor = ADC(Pin(PIN_TURBIDITY))

# DS18B20
ds_pin = Pin(PIN_DS18B20)
ow = onewire.OneWire(ds_pin)
ds = ds18x20.DS18X20(ow)

# ============ KALIBRASI pH FINAL ============
# Hasil dari metode rata-rata + koreksi offset
# pH sensor baca 7.78, tester 7.26 → offset -0.52
PH_SLOPE = -2.863341
PH_INTERCEPT = 15.169702
PH_OFFSET = -0.52      # KOREKSI OFFSET DARI VERIFIKASI

# ============ KALIBRASI TDS ============
TDS_SLOPE = 0.028       # Sesuaikan dengan data Anda

# ============ KOMPENSASI SUHU ============
SUHU_REFERENSI = 25.0
KOEFISIEN_SUHU_PH = 0.003

# ============ FUNGSI BACA ============
def baca_raw_stabil(sensor, samples=50):
    """Baca raw ADC dengan filter outlier"""
    raw_samples = []
    for _ in range(samples):
        raw_samples.append(sensor.read_u16() >> 4)
        time.sleep_ms(20)
    raw_samples.sort()
    start = int(len(raw_samples) * 0.2)
    end = int(len(raw_samples) * 0.8)
    filtered = raw_samples[start:end]
    return sum(filtered) // len(filtered)

def baca_suhu():
    """Baca suhu dari DS18B20"""
    try:
        ds.convert_temp()
        time.sleep_ms(750)
        roms = ds.scan()
        if roms:
            return ds.read_temp(roms[0])
    except:
        pass
    return 30.0

def baca_ph():
    """Baca pH dengan koreksi offset"""
    raw = baca_raw_stabil(ph_sensor)
    volt = raw * 3.3 / 4095.0
    suhu = baca_suhu()
    
    # Hitung pH kasar
    ph_kasar = PH_SLOPE * volt + PH_INTERCEPT
    
    # Tambah offset dari verifikasi
    ph_offset = ph_kasar + PH_OFFSET
    
    # Kompensasi suhu
    ph_final = ph_offset + KOEFISIEN_SUHU_PH * (suhu - SUHU_REFERENSI)
    
    # Batasi range pH 0-14
    if ph_final < 0:
        ph_final = 0
    if ph_final > 14:
        ph_final = 14
    
    return round(ph_final, 2), volt, raw, suhu

def baca_tds():
    """Baca TDS (perlu kalibrasi lanjutan)"""
    raw = baca_raw_stabil(tds_sensor)
    volt = raw * 3.3 / 4095.0
    tds = raw * TDS_SLOPE
    return round(tds), volt, raw

def baca_turbidity():
    """Baca Turbidity"""
    raw = baca_raw_stabil(turb_sensor)
    volt = raw * 3.3 / 4095.0
    
    # Konversi ke NTU (sesuaikan dengan karakteristik sensor Anda)
    if raw > 3000:
        ntu = 0.0
    elif raw < 500:
        ntu = 100.0
    else:
        ntu = (3000 - raw) / 25.0
    
    if ntu < 0:
        ntu = 0
    if ntu > 100:
        ntu = 100
    
    return round(ntu, 1), volt, raw

# ============ STATUS ============
def status_ph(ph):
    if ph < 6.5:
        return "ASAM ⚠️"
    elif ph > 8.5:
        return "BASA ⚠️"
    return "NETRAL ✅"

def kelayakan(ph, tds, ntu):
    ph_ok = 6.5 <= ph <= 8.5
    tds_ok = tds <= 600
    turb_ok = ntu <= 5
    
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
print("\n" + "="*70)
print("   WATER QUALITY MONITORING SYSTEM")
print("   Dengan koreksi offset pH = -0.52")
print("="*70)
print(f"\n📊 Parameter Kalibrasi:")
print(f"   pH = ({PH_SLOPE:.4f} × V) + {PH_INTERCEPT:.4f} + ({PH_OFFSET})")
print(f"   Kompensasi suhu: {KOEFISIEN_SUHU_PH} per °C")
print(f"   Suhu referensi: {SUHU_REFERENSI}°C")
print("="*70)

# Cek DS18B20
print("\n🔍 Mengecek sensor suhu DS18B20...")
try:
    ds.convert_temp()
    time.sleep_ms(750)
    roms = ds.scan()
    if roms:
        suhu_test = ds.read_temp(roms[0])
        print(f"✅ DS18B20 OK! Suhu: {suhu_test:.1f}°C")
    else:
        print("⚠️ DS18B20 tidak terdeteksi! Periksa kabel dan resistor 4.7kΩ")
except:
    print("⚠️ Gagal membaca DS18B20")

print("\n🔍 Stabilisasi sensor (5 detik)...")
for i in range(5):
    print(f"   {5-i} detik...")
    time.sleep(1)

print("\n" + "-"*75)
print(f"{'pH':>8} | {'TDS':>6} | {'NTU':>6} | {'Suhu':>6} | {'Status pH':>12} | {'Kelayakan':>20}")
print("-"*75)

# Moving average
ph_history = []
HISTORY = 10

while True:
    try:
        ph, ph_v, ph_raw, suhu = baca_ph()
        tds, tds_v, tds_raw = baca_tds()
        ntu, ntu_v, ntu_raw = baca_turbidity()
        
        # Moving average pH
        ph_history.append(ph)
        if len(ph_history) > HISTORY:
            ph_history.pop(0)
        ph_stabil = sum(ph_history) / len(ph_history)
        
        # Status
        status = status_ph(ph_stabil)
        layak = kelayakan(ph_stabil, tds, ntu)
        
        print(f"{ph_stabil:8.2f} | {tds:6.0f} | {ntu:6.1f} | {suhu:6.1f}°C | {status:>12} | {layak:>20}")
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n" + "-"*75)
        print("\n📊 Program selesai")
        break
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(1)
