from machine import ADC, Pin
import time

ph = ADC(Pin(26))

while True:
    total = 0
    for _ in range(50):
        total += ph.read_u16()
        time.sleep_ms(5)

    volt = (total/50) * 3.3 / 65535
    print(round(volt, 4))
    time.sleep(1)
