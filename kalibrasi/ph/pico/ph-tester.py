from machine import ADC, Pin
import time

# ==========================================
# SENSOR pH PH-4502C
# PO -> GP26 (ADC0)
# ==========================================
ph_pin = ADC(Pin(26))

# ==========================================
# FUNGSI BACA TEGANGAN
# ==========================================
def read_voltage(pin):
    total = 0
    samples = 20

    for _ in range(samples):
        total += pin.read_u16()
        time.sleep_ms(10)

    raw = total / samples
    voltage = raw * 3.3 / 65535.0

    return voltage

# ==========================================
# KLASIFIKASI pH
# ==========================================
def status_ph(ph):
    if ph < 6.5:
        return "ASAM"
    elif ph > 8.5:
        return "BASA"
    else:
        return "NETRAL"

# ==========================================
# PROGRAM UTAMA
# ==========================================
print("=" * 50)
print("   PEMBACAAN SENSOR pH PH-4502C")
print("=" * 50)

while True:

    # Baca tegangan
    v_ph = read_voltage(ph_pin)

    # ======================================
    # KALIBRASI DARI DATA TESTER
    # 3.30V -> 4.22
    # 2.925V -> 6.11
    # 2.575V -> 8.03
    # ======================================
    ph_val = (0.0833 * (v_ph ** 2)) - (5.265 * v_ph) + 20.797

    # Batasi rentang pH
    if ph_val < 0:
        ph_val = 0

    if ph_val > 14:
        ph_val = 14

    status = status_ph(ph_val)

    print("\n------------------------------")
    print("Voltage :", round(v_ph, 3), "V")
    print("pH      :", round(ph_val, 2))
    print("Status  :", status)
    print("------------------------------")

    time.sleep(1)
