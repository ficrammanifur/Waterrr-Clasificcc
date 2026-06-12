# --- oled_test_pico2.py ---
# Kode untuk menguji OLED SSD1306 pada shield Pico 2
# Konfigurasi: SDA=GP6, SCL=GP7

from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# --- Konfigurasi ---
I2C_ADDRESS = 0x3C  # GANTI dengan alamat yang Anda dapatkan dari scanner!
SDA_PIN = 6
SCL_PIN = 7

# --- Inisialisasi ---
print("Memulai inisialisasi OLED pada shield Pico 2...")
print(f"SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN}, Alamat={hex(I2C_ADDRESS)}")

i2c = I2C(1, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)

try:
    # OLED ukuran 128x64 piksel
    oled = SSD1306_I2C(128, 64, i2c, addr=I2C_ADDRESS)
    print("✓ OLED berhasil diinisialisasi!")
except Exception as e:
    print(f"✗ Gagal menginisialisasi OLED: {e}")
    raise

# --- Program Utama ---
while True:
    # Bersihkan layar
    oled.fill(0)
    
    # Tampilkan informasi koneksi
    oled.text("I2C OK!", 0, 0)
    oled.text(f"SDA=GP{SDA_PIN}", 0, 20)
    oled.text(f"SCL=GP{SCL_PIN}", 0, 35)
    oled.text(f"Addr: {hex(I2C_ADDRESS)}", 0, 50)
    oled.show()
    time.sleep(2)
    
    # Tampilkan pesan siap
    oled.fill(0)
    oled.text("Pico 2 Ready!", 15, 25)
    oled.text("Shield OK!", 25, 40)
    oled.show()
    time.sleep(2)
