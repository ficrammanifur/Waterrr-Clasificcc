"""
pH Sensor - Pico 2 (GP26)
3-Point Calibration (REAL DATA)
Moving Average + EMA Smoothing
"""

from machine import ADC, Pin
import time

# ============================================================
# KONFIGURASI
# ============================================================

ph_pin = 26
SCOUNT = 20
analog_buffer = [0] * SCOUNT
analog_index = 0

# Hasil
voltage = 0.0
ph_value = 0.0
ph_filtered = 0.0

# ============================================================
# KONSTANTA KALIBRASI REAL
# ============================================================

V4 = 3.261
PH4 = 4.00

V7 = 2.778
PH7 = 6.86

V9 = 2.387
PH9 = 9.18

# ============================================================
# FUNGSI INTERPOLASI 3 TITIK
# ============================================================

def get_ph(voltage):
    if voltage >= V7:
        # RANGE: 4.00 - 6.86
        ph = PH4 + (PH7 - PH4) * (V4 - voltage) / (V4 - V7)
    else:
        # RANGE: 6.86 - 9.18
        ph = PH7 + (PH9 - PH7) * (V7 - voltage) / (V7 - V9)
    
    return ph

# ============================================================
# INISIALISASI
# ============================================================

adc_ph = ADC(Pin(ph_pin))

# Warm-up buffer
for i in range(SCOUNT):
    analog_buffer[i] = adc_ph.read_u16()
    time.sleep_ms(20)

print("=" * 50)
print("PICO 2 pH SENSOR READY (FINAL MODE)")
print("3-POINT INTERPOLATION ACTIVE")
print(f"V4={V4:.3f}V -> pH {PH4:.2f}")
print(f"V7={V7:.3f}V -> pH {PH7:.2f}")
print(f"V9={V9:.3f}V -> pH {PH9:.2f}")
print("=" * 50)

# ============================================================
# LOOP UTAMA
# ============================================================

while True:
    # Ambil ADC
    analog_buffer[analog_index] = adc_ph.read_u16()
    analog_index += 1
    if analog_index >= SCOUNT:
        analog_index = 0
    
    # Moving average ADC
    total = 0
    for i in range(SCOUNT):
        total += analog_buffer[i]
    
    avg_adc = total / SCOUNT
    
    # Konversi ke voltage (Pico 2: 16-bit ADC, 0-3.3V)
    voltage = avg_adc * 3.3 / 65535.0
    
    # Hitung pH (INTERPOLASI)
    ph_raw = get_ph(voltage)
    
    # Smoothing pH (EMA filter)
    ph_filtered = (0.85 * ph_filtered) + (0.15 * ph_raw)
    
    # Clamp
    if ph_filtered < 0:
        ph_filtered = 0
    if ph_filtered > 14:
        ph_filtered = 14
    
    # ============================================================
    # OUTPUT
    # ============================================================
    print(f"ADC      : {avg_adc:.2f}")
    print(f"Voltage  : {voltage:.3f} V")
    print(f"pH Raw   : {ph_raw:.2f}")
    print(f"pH Smooth: {ph_filtered:.2f}")
    print("-" * 40)
    
    time.sleep(1)
