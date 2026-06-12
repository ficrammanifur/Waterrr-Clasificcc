# --- i2c_scanner.py ---
# Kode ini akan memindai bus I2C untuk menemukan alamat perangkat OLED Anda.
from machine import Pin, I2C
import time

# Pilih pasangan pin SDA dan SCL yang tersedia di shield Anda.
# Kita akan coba dengan konfigurasi yang paling memungkinkan terlebih dahulu.
SDA_PIN = 16  # (D16) untuk I2C0
SCL_PIN = 17  # (D17) untuk I2C0

print("Memulai I2C Scanner pada Pico 2...")
print(f"Menggunakan SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN}")

# Inisialisasi bus I2C
# I2C(0) merepresentasikan I2C controller 0 [citation:9]
i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000) # Frekuensi 400kHz
print("Pencarian perangkat I2C...")
devices = i2c.scan() # Fungsi inti untuk scanning

if devices:
    print(f"✓ Ditemukan {len(devices)} perangkat I2C:")
    for device in devices:
        # Tampilkan alamat dalam format heksadesimal (contoh: 0x3c)
        # dan format desimal (contoh: 60)
        print(f"  - Alamat: {hex(device)} (Desimal: {device})")
else:
    print("✗ Tidak ada perangkat I2C yang ditemukan.")
    print("Periksa kembali koneksi kabel dan pastikan resistor pull-up 4.7kΩ terpasang.")
