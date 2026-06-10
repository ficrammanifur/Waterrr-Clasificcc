# DHT22 Test dengan Pull-up Internal
from machine import Pin
import dht
import time

PIN_DHT = 20

# Inisialisasi dengan pull-up internal
sensor = dht.DHT22(Pin(PIN_DHT, Pin.IN, Pin.PULL_UP))

print("DHT22 Test - GPIO 20 dengan PULL_UP")
print("Tekan Ctrl+C untuk berhenti\n")

while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        print(f"Suhu: {temp:.1f}°C  |  Kelembaban: {hum:.1f}%")
    except OSError as e:
        print(f"Gagal: {e}")
    time.sleep(2)
