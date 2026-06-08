from machine import ADC, Pin
import time

turb = ADC(Pin(28))

while True:
    raw = turb.read_u16()
    volt = raw * 3.3 / 65535

    print(round(volt,3))
    time.sleep(0.5)
