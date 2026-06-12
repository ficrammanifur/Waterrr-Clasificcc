from machine import ADC, Pin
import time

tds = ADC(Pin(27))

while True:

    raw = tds.read_u16()
    volt = raw * 3.3 / 65535

    # Persamaan sementara
    ppm = (900 * volt) - 500

    if ppm < 0:
        ppm = 0

    print("================")
    print("Volt :", round(volt,3))
    print("TDS  :", round(ppm,1), "ppm")
    print("================")

    time.sleep(1)
