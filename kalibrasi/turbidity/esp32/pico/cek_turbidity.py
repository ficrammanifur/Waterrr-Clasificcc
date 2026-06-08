# cek_turbidity.py - Diagnostik sensor turbidity
from machine import ADC, Pin
import time

turb_sensor = ADC(Pin(28))

print("=== DIAGNOSTIK SENSOR TURBIDITY ===")
print("\nCelupkan sensor ke:")
print("1. Air JERNIH (botol Aqua)")
print("2. Air KERUH (campur tanah/susu)\n")

while True:
    raw = turb_sensor.read_u16()
    volt = raw * 3.3 / 65535.0
    
    # Hitung NTU dengan berbagai rumus
    ntu1 = (3.3 - volt) * 100      # Rumus standar
    ntu2 = (3.3 - volt) * 500      # Sensitif lebih tinggi
    ntu3 = (volt * 100)            # Alternatif
    
    print(f"Raw: {raw:5d} | Volt: {volt:.4f}V | NTU(standar): {ntu1:.1f} | NTU(sensitif): {ntu2:.1f}")
    time.sleep(0.5)
