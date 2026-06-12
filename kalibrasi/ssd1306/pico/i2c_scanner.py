# --- i2c_scanner_pico2.py ---
# Kode ini akan memindai bus I2C untuk menemukan alamat perangkat OLED Anda.
# Menggunakan konfigurasi: SDA=GP6, SCL=GP7

from machine import Pin, I2C
import time

# Konfigurasi pin sesuai shield Anda
SDA_PIN = 6  # GP6 (Pin 6 pada shield)
SCL_PIN = 7  # GP7 (Pin 7 pada shield)

print("Memulai I2C Scanner pada Pico 2...")
print(f"Menggunakan SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN}")
print("=" * 40)

# Inisialisasi bus I2C
# Gunakan I2C0 atau I2C1? GP6 dan GP7 adalah I2C1 [citation:2][citation:9]
i2c = I2C(1, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)

print("Pencarian perangkat I2C...")
devices = i2c.scan() # Fungsi inti untuk scanning

if devices:
    print(f"✓ Ditemukan {len(devices)} perangkat I2C:")
    for device in devices:
        # Tampilkan alamat dalam format heksadesimal (contoh: 0x3c)
        print(f"  - Alamat: {hex(device)} (Desimal: {device})")
        
        # Informasi tambahan untuk OLED SSD1306
        if device == 0x3C:
            print("    >> Ini adalah alamat standar OLED SSD1306 (0x3C)")
        elif device == 0x3D:
            print("    >> Ini adalah alamat alternatif OLED SSD1306 (0x3D)")
else:
    print("✗ Tidak ada perangkat I2C yang ditemukan.")
    print("Periksa kembali koneksi kabel.")
