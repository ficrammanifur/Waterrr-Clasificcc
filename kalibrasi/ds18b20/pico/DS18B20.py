# ds18b20_pico2.py - Membaca suhu dari sensor DS18B20
# Menggunakan GPIO 16 (Pin D16 pada shield)

from machine import Pin
import onewire, ds18x20
import time

# --- 1. Inisialisasi Pin dan Sensor ---
# Ganti angka 16 jika Anda menggunakan pin selain D16
PIN_DS18B20 = 16

print(f"Memulai inisialisasi sensor DS18B20 pada GPIO {PIN_DS18B20}...")
sensor_pin = Pin(PIN_DS18B20)
ow = onewire.OneWire(sensor_pin)
ds = ds18x20.DS18X20(ow)

# --- 2. Mendeteksi Sensor ---
# Scan untuk mencari sensor yang terhubung
roms = ds.scan()

if not roms:
    print("=" * 40)
    print("⚠️  PERINGATAN PENTING ⚠️")
    print("Tidak ada sensor DS18B20 yang terdeteksi!")
    print("Mohon periksa hal-hal berikut:")
    print("1. Pastikan Resistor PULL-UP 4.7kΩ terpasang dengan benar antara VCC dan DATA.")
    print("2. Periksa kembali sambungan kabel (VCC, GND, DATA).")
    print("3. Pastikan sensor dalam kondisi berfungsi baik.")
    print("=" * 40)
else:
    print(f"✅ Berhasil! Ditemukan {len(roms)} sensor DS18B20.")
    print("Memulai pembacaan suhu...")
    print("-" * 30)

    # --- 3. Loop Membaca Suhu ---
    while True:
        try:
            # Memulai proses konversi suhu
            ds.convert_temp()
            # Waktu tunggu minimal 750ms agar konversi 12-bit selesai
            time.sleep_ms(750)

            # Membaca dan menampilkan suhu dari setiap sensor yang ditemukan
            for rom in roms:
                suhu = ds.read_temp(rom)
                print(f"Suhu: {suhu:.2f} °C")
            
            print("-" * 30)
            time.sleep(2) # jeda 2 detik sebelum pembacaan berikutnya

        except KeyboardInterrupt:
            print("\nProgram dihentikan oleh pengguna.")
            break
        except Exception as e:
            print(f"Terjadi error saat membaca sensor: {e}")
            time.sleep(2)
