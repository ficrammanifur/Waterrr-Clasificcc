from machine import ADC, Pin
import time

tds = ADC(Pin(27))

while True:
    raw = tds.read_u16()
    volt = raw * 3.3 / 65535

    print(round(volt,3))
    time.sleep(1)
