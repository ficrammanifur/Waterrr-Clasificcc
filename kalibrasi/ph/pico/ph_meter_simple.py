# ph_meter_simple.py - Paling sederhana, tanpa buffer
from machine import ADC, Pin
import time

ph_sensor = ADC(Pin(26))

# Data kalibrasi
KALIBRASI = [
    (3.2992, 4.01),
    (2.9454, 6.86),
    (2.5705, 9.18)
]

def volt_ke_ph(volt):
    """Konversi tegangan ke pH"""
    if volt >= KALIBRASI[0][0]:
        v1, ph1 = KALIBRASI[0]
        v2, ph2 = KALIBRASI[1]
        slope = (ph2 - ph1) / (v2 - v1)
        return ph1 + slope * (volt - v1)
    elif volt <= KALIBRASI[-1][0]:
        v1, ph1 = KALIBRASI[1]
        v2, ph2 = KALIBRASI[2]
        slope = (ph2 - ph1) / (v2 - v1)
        return ph1 + slope * (volt - v1)
    else:
        for i in range(len(KALIBRASI) - 1):
            if KALIBRASI[i+1][0] <= volt <= KALIBRASI[i][0]:
                v1, ph1 = KALIBRASI[i]
                v2, ph2 = KALIBRASI[i+1]
                slope = (ph2 - ph1) / (v2 - v1)
                return ph1 + slope * (volt - v1)
    return 7.0

def baca_ph(samples=50):
    """Baca pH dengan averaging"""
    total = 0
    for _ in range(samples):
        total += ph_sensor.read_u16()
        time.sleep_ms(5)
    avg_raw = total / samples
    volt = avg_raw * 3.3 / 65535.0
    return round(volt_ke_ph(volt), 2), volt

print("\n=== pH METER SEDERHANA ===")
print("Kalibrasi: pH 4.01, 6.86, 9.18")
print("Tekan Ctrl+C untuk berhenti\n")

while True:
    try:
        ph, volt = baca_ph()
        print(f"Tegangan: {volt:.4f} V  |  pH: {ph:.2f}")
        time.sleep(1)
    except KeyboardInterrupt:
        print("\nSelesai.")
        break
