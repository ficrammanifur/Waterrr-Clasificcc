from machine import ADC
from time import sleep
import math

# =====================================
# Raspberry Pi Pico 2
# pH Sensor Auto Calibration
# GPIO26 = ADC0
# =====================================

adc = ADC(26)

# -----------------------------
# Setting
# -----------------------------
STABILIZE_TIME = 120      # detik
SAMPLE_DELAY = 0.1        # 100 ms
SAMPLE_COUNT = 200        # 20 detik sampling

# -----------------------------
# Baca Tegangan
# -----------------------------
def read_voltage():

    raw = adc.read_u16()
    voltage = raw * 3.3 / 65535.0

    return raw, voltage

# -----------------------------
# Statistik
# -----------------------------
def statistics(data):

    data.sort()

    # Median Filter
    median = data[len(data)//2]

    # Buang 10% data atas & bawah
    cut = int(len(data) * 0.1)

    filtered = data[cut:-cut]

    average = sum(filtered) / len(filtered)

    minimum = min(filtered)
    maximum = max(filtered)

    variance = 0

    for x in filtered:
        variance += (x-average)**2

    variance /= len(filtered)

    std = math.sqrt(variance)

    return average, minimum, maximum, median, std

# -----------------------------
# Kalibrasi
# -----------------------------
def calibrate(buffer_name):

    print("\n")
    print("==========================================")
    print("Masukkan Probe ke Buffer pH", buffer_name)
    print("Tekan ENTER jika sudah siap...")
    input()

    print("\nMenunggu Stabilisasi...")

    for i in range(STABILIZE_TIME,0,-1):

        if i % 10 == 0 or i <= 10:
            print("Sisa :", i, "detik")

        sleep(1)

    print("\nMengambil", SAMPLE_COUNT, "sample...\n")

    voltages = []

    for i in range(SAMPLE_COUNT):

        raw, voltage = read_voltage()

        voltages.append(voltage)

        if (i+1)%20==0:
            print("Progress :", i+1,"/",SAMPLE_COUNT)

        sleep(SAMPLE_DELAY)

    avg, vmin, vmax, med, std = statistics(voltages)

    print("\n========== HASIL ==========")
    print("Buffer pH :", buffer_name)
    print("Average   :", round(avg,5),"Volt")
    print("Median    :", round(med,5),"Volt")
    print("Minimum   :", round(vmin,5),"Volt")
    print("Maximum   :", round(vmax,5),"Volt")
    print("Std Dev   :", round(std,6),"Volt")

    if std < 0.003:
        print("Kualitas  : Sangat Stabil")

    elif std < 0.008:
        print("Kualitas  : Stabil")

    elif std < 0.015:
        print("Kualitas  : Cukup")

    else:
        print("Kualitas  : Banyak Noise")

    print("===========================\n")

    return avg

# =====================================
# MAIN
# =====================================

print("=========================================")
print("     AUTO PH CALIBRATION")
print(" Raspberry Pi Pico 2")
print("=========================================")

V4 = calibrate("4.01")

V7 = calibrate("6.86")

V9 = calibrate("9.18")

print("\n\n======================================")
print("AUTO GENERATED CALIBRATION")
print("======================================")

print("V4  = %.5f" % V4)
print("PH4 = 4.01\n")

print("V7  = %.5f" % V7)
print("PH7 = 6.86\n")

print("V9  = %.5f" % V9)
print("PH9 = 9.18")

print("======================================")
print("Selesai.")
