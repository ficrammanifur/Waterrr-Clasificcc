from machine import ADC, Pin
import time

ph_pin = ADC(Pin(26))

def read_voltage(pin):
    total = 0

    for _ in range(30):
        total += pin.read_u16()
        time.sleep_ms(5)

    raw = total / 30
    voltage = raw * 3.3 / 65535

    return voltage

def status_ph(ph):

    if ph < 6.5:
        return "ASAM"

    elif ph > 8.5:
        return "BASA"

    else:
        return "NETRAL"

while True:

    v = read_voltage(ph_pin)

    # Kalibrasi baru
    ph = (-0.4862 * (v ** 2)) - (4.2800 * v) + 23.4245

    if ph < 0:
        ph = 0

    if ph > 14:
        ph = 14

    print("======================")
    print("Voltage :", round(v,4), "V")
    print("pH      :", round(ph,2))
    print("Status  :", status_ph(ph))
    print("======================")

    time.sleep(1)
