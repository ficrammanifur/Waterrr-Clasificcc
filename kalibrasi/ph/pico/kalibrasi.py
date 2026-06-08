# rekam_kalibrasi.py - Rekam data kalibrasi
from machine import ADC, Pin
import time

ph_sensor = ADC(Pin(26))

def baca_tegangan(samples=100):
    total = 0
    for _ in range(samples):
        total += ph_sensor.read_u16()
        time.sleep_ms(5)
    avg_raw = total / samples
    volt = avg_raw * 3.3 / 65535.0
    return volt

print("=== REKAM DATA KALIBRASI pH ===")
print("Celupkan sensor ke larutan buffer pH 4.01")
input("Tekan ENTER setelah stabil...")

v4 = baca_tegangan()
print(f"Tegangan pH 4.01: {v4:.4f} V\n")

print("Celupkan sensor ke larutan buffer pH 6.86")
input("Tekan ENTER setelah stabil...")

v7 = baca_tegangan()
print(f"Tegangan pH 6.86: {v7:.4f} V\n")

print("Celupkan sensor ke larutan buffer pH 9.18")
input("Tekan ENTER setelah stabil...")

v9 = baca_tegangan()
print(f"Tegangan pH 9.18: {v9:.4f} V\n")

print("\n=== HASIL KALIBRASI ===")
print(f"kalibrasi_points = [")
print(f"    ({v4:.3f}, 4.01),")
print(f"    ({v7:.3f}, 6.86),")
print(f"    ({v9:.3f}, 9.18)")
print(f"]")
