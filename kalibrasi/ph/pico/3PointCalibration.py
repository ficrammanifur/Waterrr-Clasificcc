from machine import ADC
from time import sleep_ms

# ==========================================
# Raspberry Pi Pico 2
# pH Meter
# 3 Point Calibration
# ==========================================

ph_sensor = ADC(26)

# ==========================================
# HASIL KALIBRASI
# ==========================================

V4  = 3.29406
PH4 = 4.01

V7  = 2.94870
PH7 = 6.86

V9  = 2.62498
PH9 = 9.18

# ==========================================
# FILTER
# ==========================================

SCOUNT = 20

buffer = [0] * SCOUNT
index = 0

ph_filtered = None


# ==========================================
# Fungsi Interpolasi
# ==========================================

def get_ph(voltage):

    # pH 4.01 -> 6.86
    if voltage >= V7:

        ph = PH4 + (PH7 - PH4) * (V4 - voltage) / (V4 - V7)

    # pH 6.86 -> 9.18
    else:

        ph = PH7 + (PH9 - PH7) * (V7 - voltage) / (V7 - V9)

    return ph


# ==========================================
# Warm Up
# ==========================================

for i in range(SCOUNT):
    buffer[i] = ph_sensor.read_u16()
    sleep_ms(20)

print("=" * 50)
print("      Raspberry Pi Pico 2 pH Meter")
print("        3 Point Calibration")
print("=" * 50)

while True:

    buffer[index] = ph_sensor.read_u16()

    index += 1

    if index >= SCOUNT:
        index = 0

    avg_adc = sum(buffer) / SCOUNT

    voltage = avg_adc * 3.3 / 65535.0

    ph_raw = get_ph(voltage)

    # EMA
    if ph_filtered is None:
        ph_filtered = ph_raw
    else:
        ph_filtered = (0.85 * ph_filtered) + (0.15 * ph_raw)

    # Clamp
    if ph_filtered < 0:
        ph_filtered = 0

    if ph_filtered > 14:
        ph_filtered = 14

    print(
        "ADC:{:6.0f} | Voltage:{:.3f}V | pH Raw:{:.2f} | pH:{:.2f}".format(
            avg_adc,
            voltage,
            ph_raw,
            ph_filtered
        )
    )

    sleep_ms(1000)
