from machine import ADC
import time

# =====================================
# Raspberry Pi Pico pH Sensor
# GPIO26 (ADC0)
# Moving Average + EMA
# =====================================

ph_sensor = ADC(26)

# ================================
# Moving Average
# ================================
SCOUNT = 20
analog_buffer = []

for i in range(SCOUNT):
    analog_buffer.append(ph_sensor.read_u16())
    time.sleep(0.02)

analog_index = 0

# ================================
# Kalibrasi 3 Titik
# ================================
V4  = 3.290
PH4 = 4.00

V7  = 2.870
PH7 = 6.86

V9  = 2.522
PH9 = 9.18

# EMA
ph_filtered = 7.0


def get_ph(voltage):
    if voltage >= V7:
        # Interpolasi 4 -> 6.86
        return PH4 + (PH7 - PH4) * (V4 - voltage) / (V4 - V7)
    else:
        # Interpolasi 6.86 -> 9.18
        return PH7 + (PH9 - PH7) * (V7 - voltage) / (V7 - V9)


print("====================================")
print("PICO pH SENSOR READY")
print("3-POINT INTERPOLATION ACTIVE")
print("====================================")

while True:

    # Baca ADC
    analog_buffer[analog_index] = ph_sensor.read_u16()
    analog_index = (analog_index + 1) % SCOUNT

    # Moving Average
    avg_adc = sum(analog_buffer) / SCOUNT

    # Konversi ke Tegangan
    voltage = avg_adc * (3.3 / 65535.0)

    # Hitung pH
    ph_raw = get_ph(voltage)

    # EMA Filter
    ph_filtered = (0.85 * ph_filtered) + (0.15 * ph_raw)

    # Clamp
    if ph_filtered < 0:
        ph_filtered = 0

    if ph_filtered > 14:
        ph_filtered = 14

    print(
        "ADC: {:.0f} | Voltage: {:.3f} V | pH Raw: {:.2f} | pH Smooth: {:.2f}"
        .format(avg_adc, voltage, ph_raw, ph_filtered)
    )

    time.sleep(1)
