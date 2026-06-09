# collect_data_mlp_fixed_memory.py - Versi hemat memori
from machine import ADC, Pin
import time
import gc  # Garbage collector

# ============================================
# INISIALISASI SENSOR
# ============================================
ph_sensor = ADC(Pin(26))
tds_sensor = ADC(Pin(27))
turb_sensor = ADC(Pin(28))

# ============================================
# KALIBRASI
# ============================================
KALIBRASI_PH_LAMA = [
    (3.2992, 4.01),
    (2.9454, 6.86),
    (2.5705, 9.18)
]

PH_OFFSET = -1.03
TDS_SCALE = 0.5747

# ============================================
# DATA DARI TESTER
# ============================================
TARGET_TDS = {
    "Aqua": 109, "Le Minerale": 148, "Cleo": 8, "Amidis": 2,
    "Pristine": 104, "Vit": 161, "Prima": 172, "Club": 71,
    "Crystalline": 75, "Aquaviva": 101
}

TARGET_PH = {
    "Aqua": 7.93, "Le Minerale": 7.86, "Cleo": 6.75, "Amidis": 5.18,
    "Pristine": 8.58, "Vit": 7.99, "Prima": 7.85, "Club": 7.93,
    "Crystalline": 7.52, "Aquaviva": 7.38
}

SAMPEL_AIR_MINERAL = [
    "Aqua", "Le Minerale", "Cleo", "Amidis", "Pristine",
    "Vit", "Prima", "Club", "Crystalline", "Aquaviva"
]

# ============================================
# FUNGSI BACA SENSOR
# ============================================
def baca_raw(sensor, samples=50):
    total = 0
    for _ in range(samples):
        total += sensor.read_u16()
        time.sleep_ms(5)
    return total / samples

def baca_ph_raw():
    raw = baca_raw(ph_sensor, 50)
    volt = raw * 3.3 / 65535.0
    
    if volt >= KALIBRASI_PH_LAMA[0][0]:
        v1, p1 = KALIBRASI_PH_LAMA[0]
        v2, p2 = KALIBRASI_PH_LAMA[1]
        ph = p1 + (p2 - p1) * (volt - v1) / (v2 - v1)
    elif volt <= KALIBRASI_PH_LAMA[2][0]:
        v1, p1 = KALIBRASI_PH_LAMA[1]
        v2, p2 = KALIBRASI_PH_LAMA[2]
        ph = p1 + (p2 - p1) * (volt - v1) / (v2 - v1)
    else:
        for i in range(2):
            if KALIBRASI_PH_LAMA[i+1][0] <= volt <= KALIBRASI_PH_LAMA[i][0]:
                v1, p1 = KALIBRASI_PH_LAMA[i]
                v2, p2 = KALIBRASI_PH_LAMA[i+1]
                ph = p1 + (p2 - p1) * (volt - v1) / (v2 - v1)
                break
        else:
            ph = 7.0
    return raw, volt, ph

def baca_ph():
    raw, volt, ph_raw = baca_ph_raw()
    ph_terkoreksi = ph_raw + PH_OFFSET
    return raw, volt, round(ph_terkoreksi, 2)

def baca_tds():
    raw = baca_raw(tds_sensor, 50)
    volt = raw * 3.3 / 65535.0
    raw_terkoreksi = raw * TDS_SCALE
    volt_terkoreksi = raw_terkoreksi * 3.3 / 65535.0
    return raw_terkoreksi, volt_terkoreksi

def baca_turbidity():
    raw = baca_raw(turb_sensor, 50)
    volt = raw * 3.3 / 65535.0
    
    if volt > 3.0:
        ntu = 0
    elif volt < 0.5:
        ntu = 300
    else:
        ntu = (3.3 - volt) * 50
        if ntu < 0:
            ntu = 0
        if ntu > 300:
            ntu = 300
    return raw, volt, round(ntu, 1)

# ============================================
# FUNGSI SIMPAN KE CSV (LANGSUNG, TANPA SIMPAN DI RAM)
# ============================================
def kumpulkan_data(sampel_name, target_tds, target_ph, jumlah=100):
    print("\n📊 MENGUMPULKAN DATA: {}".format(sampel_name))
    print("   Target TDS: {} ppm, Target pH: {}".format(target_tds, target_ph))
    
    nama_file = "data_{}.csv".format(sampel_name.replace(" ", "_"))
    
    input("\n🔹 Celupkan sensor ke {} lalu ENTER...".format(sampel_name))
    print("   Menunggu stabil (5 detik)...")
    time.sleep(5)
    
    # Buka file dan tulis langsung (tanpa simpan di RAM)
    with open(nama_file, 'w') as f:
        # Header
        f.write("sampel,ph_raw,ph_volt,ph_value,tds_raw,tds_volt,turb_raw,turb_volt,turb_ntu,target_tds,target_ph,target_kelayakan\n")
        
        for i in range(jumlah):
            ph_raw, ph_volt, ph_value = baca_ph()
            tds_raw, tds_volt = baca_tds()
            turb_raw, turb_volt, turb_ntu = baca_turbidity()
            
            # Tulis langsung ke file
            line = "{},{:.2f},{:.4f},{:.2f},{:.2f},{:.4f},{:.2f},{:.4f},{:.1f},{},{},{}\n".format(
                sampel_name, ph_raw, ph_volt, ph_value,
                tds_raw, tds_volt, turb_raw, turb_volt,
                turb_ntu, target_tds, target_ph, 1 if target_tds < 500 else 0
            )
            f.write(line)
            
            if (i+1) % 20 == 0:
                print("   [{}/{}] pH:{:.2f} | TDS_raw:{:.0f} | NTU:{:.1f}".format(
                    i+1, jumlah, ph_value, tds_raw, turb_ntu))
            
            time.sleep(0.1)
            
            # Bebaskan memori setiap 100 data
            if (i+1) % 100 == 0:
                gc.collect()
    
    print("✅ Data tersimpan: {} ({} sampel)".format(nama_file, jumlah))
    gc.collect()
    return True

def kumpulkan_semua_data(jumlah_per_sampel=100):
    print("\n" + "="*50)
    print("   PENGUMPULAN DATA SEMUA AIR MINERAL")
    print("   Total: {} sampel x {} data = {} data".format(
        len(SAMPEL_AIR_MINERAL), jumlah_per_sampel, 
        len(SAMPEL_AIR_MINERAL) * jumlah_per_sampel))
    print("="*50)
    
    for i, sampel in enumerate(SAMPEL_AIR_MINERAL, 1):
        target_tds = TARGET_TDS.get(sampel, 0)
        target_ph = TARGET_PH.get(sampel, 0)
        
        print("\n🟢 Sampel {}/{}: {}".format(i, len(SAMPEL_AIR_MINERAL), sampel))
        print("-"*40)
        
        kumpulkan_data(sampel, target_tds, target_ph, jumlah_per_sampel)
        
        print("\n   ✅ Selesai {}: {} data".format(sampel, jumlah_per_sampel))
        
        if sampel != SAMPEL_AIR_MINERAL[-1]:
            input("\n▶️ Tekan ENTER untuk lanjut ke sampel berikutnya...")
        
        gc.collect()  # Bebaskan memori setiap selesai sampel
    
    print("\n🎉 SELESAI! Semua data tersimpan dalam file CSV terpisah.")
    return True

# ============================================
# PROGRAM UTAMA
# ============================================
print("\n" + "="*50)
print("   PENGUMPULAN DATA UNTUK MLP")
print("   VERSI HEMAT MEMORI")
print("="*50)
print("\n✅ Koreksi yang digunakan:")
print("   PH_OFFSET = {:.2f}".format(PH_OFFSET))
print("   TDS_SCALE = {:.4f}".format(TDS_SCALE))
print("="*50)

# Tes cepat dulu
print("\n🔍 TEST CEPAT DENGAN AQUA")
input("Celupkan sensor ke Aqua, lalu ENTER...")
time.sleep(3)

ph_raw, ph_volt, ph_value = baca_ph()
tds_raw, tds_volt = baca_tds()

print("\n📊 HASIL TEST:")
print("   pH : {:.2f} (target 7.93)".format(ph_value))
print("   TDS_raw: {:.0f}".format(tds_raw))

if abs(ph_value - 7.93) < 0.2:
    print("\n✅ KOREKSI BERHASIL!")
    
    lanjut = input("\nLanjut kumpulkan data semua sampel? (y/n): ")
    if lanjut.lower() == 'y':
        jumlah = int(input("Jumlah data per sampel (50-200): ") or "100")
        if jumlah > 200:
            print("⚠️ Max 200 data per sampel agar tidak kehabisan memori")
            jumlah = 100
        kumpulkan_semua_data(jumlah)
    else:
        # Kumpulkan satu sampel saja
        jumlah = int(input("Jumlah data (50-200): ") or "100")
        sampel = input("Nama sampel: ")
        target_tds = int(input("Target TDS (ppm): "))
        target_ph = float(input("Target pH: "))
        kumpulkan_data(sampel, target_tds, target_ph, jumlah)
else:
    print("\n⚠️ Test gagal, periksa sensor!")
