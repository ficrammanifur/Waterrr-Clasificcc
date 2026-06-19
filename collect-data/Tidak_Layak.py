from machine import ADC, Pin
import time
import onewire, ds18x20

# ====================================================
# PENGATURAN NAMA FILE KHUSUS FASE 2
# ====================================================
NAMA_FILE = "Dataset_Air_Tidak_Layak.csv" 
# ====================================================

# ===== SETUP SENSOR =====
tds_sensor = ADC(Pin(27))
ph_sensor = ADC(Pin(26))
turb_sensor = ADC(Pin(28))
ds_pin = Pin(16)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()

def read_temp():
    ds_sensor.convert_temp()
    time.sleep(0.75)
    return ds_sensor.read_temp(roms[0])

def read_voltage(pin, n=10):
    total = 0
    for _ in range(n):
        total += pin.read_u16()
        time.sleep_ms(5)
    raw = total / n
    return raw, raw * 3.3 / 65535

# ===== KALIBRASI TURBIDITY =====
NILAI_JERNIH = 2150
NILAI_KERUH = 200
RANGE_NILAI = NILAI_JERNIH - NILAI_KERUH

def baca_ntu():
    raw_16bit = turb_sensor.read_u16()
    nilai = raw_16bit >> 4
    if nilai >= NILAI_JERNIH:
        ntu = 0.0
    elif nilai <= NILAI_KERUH:
        ntu = 100.0
    else:
        ntu = (NILAI_JERNIH - nilai) * 100.0 / RANGE_NILAI
    tegangan = nilai * 3.3 / 4095.0
    return nilai, tegangan, ntu

# ====================================================
# KATEGORI BARU KHUSUS AIR TIDAK LAYAK
# ====================================================
JENIS_AIR = [
    "1=Air Mentah", 
    "2=Tercemar Asam (Cuka)", 
    "3=Tercemar Basa (Kapur)",
    "4=TDS Ekstrem (Garam)", 
    "5=Keruh/Organik", 
    "6=Lainnya"
]

print(f"=== DATASET COLLECTOR FASE 2 - MENYIMPAN KE: {NAMA_FILE} ===")
print("Untuk tiap sample: masukkan nama, pH, PPM (tester), kelayakan, jenis air")
print("NTU dihitung otomatis dari sensor")
print("Kode jenis air:")
for j in JENIS_AIR:
    print("  ", j)
print()

# Header CSV (Struktur sama persis dengan dataset layak)
try:
    with open(NAMA_FILE, "x") as f:
        f.write("nama_sample,ph_label,ppm_label,status_air,kelayakan,jenis_air,raw_ph,volt_ph,raw_tds,volt_tds,comp_volt_tds,raw_turb,volt_turb,ntu_sensor,suhu\n")
except OSError:
    pass

def status_dari_ph(ph):
    if ph < 6.5:
        return "ASAM"
    elif ph > 8.5:
        return "BASA"
    else:
        return "NETRAL"

while True:
    nama = input("\nNama sample (atau 'done' untuk selesai): ")
    if nama.strip().lower() == "done":
        break

    try:
        ph_label = float(input("  pH tester    : "))
        ppm_label = float(input("  PPM tester   : "))
        # Default otomatis untuk fase ini biasanya TIDAK LAYAK, tapi tetap diminta input untuk validasi
        kelayakan_in = input("  Kelayakan (L=LAYAK / T=TIDAK LAYAK): ").strip().upper()
        kelayakan = "LAYAK" if kelayakan_in == "L" else "TIDAK LAYAK"
        jenis_in = int(input("  Jenis air (pilih nomor 1-6 dari list di atas): "))
        jenis_air = JENIS_AIR[jenis_in - 1].split("=")[1]
    except (ValueError, IndexError):
        print("  Input tidak valid, ulangi sample ini.")
        continue

    status_air = status_dari_ph(ph_label)

    print(f"  -> Status: {status_air} | Kelayakan: {kelayakan} | Jenis: {jenis_air}")
    print("  Tunggu probe settle (15 detik)...")
    time.sleep(15)

    print("  Mengambil 200 sample...")

    with open(NAMA_FILE, "a") as f:
        for i in range(200):
            temperature = read_temp()

            raw_ph, volt_ph = read_voltage(ph_sensor, n=10)
            raw_tds, volt_tds = read_voltage(tds_sensor, n=10)
            raw_turb, volt_turb, ntu_sensor = baca_ntu()

            comp_coef = 1.0 + 0.02 * (temperature - 25.0)
            comp_volt_tds = volt_tds / comp_coef

            line = (f"{nama},{ph_label},{ppm_label},"
                    f"{status_air},{kelayakan},{jenis_air},"
                    f"{raw_ph:.2f},{volt_ph:.4f},{raw_tds:.2f},{volt_tds:.4f},{comp_volt_tds:.4f},"
                    f"{raw_turb},{volt_turb:.4f},{ntu_sensor:.2f},{temperature:.2f}\n")
            f.write(line)

            if (i + 1) % 50 == 0:
                print("    ", i + 1, "/200")

    print(f"  ==> Sample '{nama}' selesai, 200 baris tersimpan.")
    print("  ⚠️ PENTING: Bilas probe pH & TDS dengan air bersih 2x sebelum lanjut!")

print("\n=== SELESAI ===")
print(f"Dataset tersimpan di {NAMA_FILE}")
