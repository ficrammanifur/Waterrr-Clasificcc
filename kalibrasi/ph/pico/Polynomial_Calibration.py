from machine import ADC
from time import sleep_ms

# ==========================================
# Raspberry Pi Pico 2
# pH Meter
# Polynomial Calibration (Order 2)
# ==========================================

ph_sensor = ADC(26)

# ==========================================
# HASIL KALIBRASI KAMU
# ==========================================

# Persamaan:
#
# pH = aV² + bV + c
#

A = -2.18513
B = -1.36782
C = 32.16659

# ==========================================
# FILTER
# ==========================================

SCOUNT = 20

buffer = [0]*SCOUNT
index = 0

ph_filtered = None

# ==========================================
# Moving Average
# ==========================================

for i in range(SCOUNT):
    buffer[i] = ph_sensor.read_u16()
    sleep_ms(20)

print("="*45)
print("Raspberry Pi Pico 2")
print("Polynomial pH Meter")
print("="*45)

while True:

    buffer[index] = ph_sensor.read_u16()

    index += 1

    if index >= SCOUNT:
        index = 0

    avg_adc = sum(buffer) / SCOUNT

    voltage = avg_adc * 3.3 / 65535.0

    # ==================================
    # Polynomial
    # ==================================

    ph_raw = A*(voltage**2) + B*voltage + C

    # EMA
    if ph_filtered is None:
        ph_filtered = ph_raw
    else:
        ph_filtered = 0.85*ph_filtered + 0.15*ph_raw

    # Clamp

    if ph_filtered < 0:
        ph_filtered = 0

    if ph_filtered > 14:
        ph_filtered = 14

    print(
        "ADC:{:6.0f}  Voltage:{:.3f}V  pH:{:.2f}"
        .format(avg_adc, voltage, ph_filtered)
    )

    sleep_ms(1000)
