from machine import ADC, Pin
import time
import onewire, ds18x20

# ===== SETUP =====
tds_sensor = ADC(Pin(27))
ds_pin = Pin(16)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()

# ===== HASIL KALIBRASI (KUADRATIK) =====
CAL_A = 21610.744
CAL_B = -17487.274
CAL_C = 3383.3512

def read_temp():
    ds_sensor.convert_temp()
    time.sleep(0.75)
    return ds_sensor.read_temp(roms[0])

while True:
    temperature = read_temp()

    samples = []
    for _ in range(50):
        samples.append(tds_sensor.read_u16())
        time.sleep(0.01)

    raw = sum(samples) / len(samples)
    voltage = raw * 3.3 / 65535

    compensation_coefficient = 1.0 + 0.02 * (temperature - 25.0)
    compensated_voltage = voltage / compensation_coefficient

    tds = CAL_A * (compensated_voltage ** 2) + CAL_B * compensated_voltage + CAL_C
    if tds < 0:
        tds = 0

    print("Temp     :", round(temperature, 2), "C")
    print("Voltage  :", round(voltage, 3), "V")
    print("TDS      :", round(tds, 2), "ppm")
    print("------------------------")
