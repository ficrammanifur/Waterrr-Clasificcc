from machine import ADC, Pin
import time
import onewire, ds18x20

# ===== SETUP =====
tds_sensor = ADC(Pin(27))
ds_pin = Pin(16)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()

def read_temp():
    ds_sensor.convert_temp()
    time.sleep(0.75)
    return ds_sensor.read_temp(roms[0])

def read_compvolt():
    temperature = read_temp()
    samples = []
    for _ in range(50):
        samples.append(tds_sensor.read_u16())
        time.sleep(0.01)
    raw = sum(samples) / len(samples)
    voltage = raw * 3.3 / 65535
    comp_coef = 1.0 + 0.02 * (temperature - 25.0)
    comp_voltage = voltage / comp_coef
    return comp_voltage, voltage, temperature

# ===== KALIBRASI OTOMATIS =====
print("=== MODE KALIBRASI OTOMATIS ===")
print("Urutkan larutan dari PPM TERENDAH ke TERTINGGI")
print("Ketik 'done' jika sudah selesai input semua titik\n")

cal_points = []

while True:
    inp = input("\nMasukkan nilai PPM tester (atau 'done' untuk selesai): ")

    if inp.strip().lower() == "done":
        break

    try:
        ppm = float(inp)
    except ValueError:
        print("Input tidak valid, coba lagi.")
        continue

    print("Tunggu probe settle (15 detik)...")
    for i in range(15, 0, -1):
        print(" ", i, "...")
        time.sleep(1)

    print("Mulai sampling...")

    readings = []
    stable_window = 8
    max_readings = 40
    threshold = 0.005

    while len(readings) < max_readings:
        comp_v, raw_v, temp = read_compvolt()
        readings.append(comp_v)
        print("  CompVolt:", round(comp_v, 4), "| Temp:", round(temp, 2), "C  (n =", len(readings), ")")

        if len(readings) >= stable_window:
            recent = readings[-stable_window:]
            avg = sum(recent) / len(recent)
            variance = sum((x - avg) ** 2 for x in recent) / len(recent)
            std_dev = variance ** 0.5

            if std_dev < threshold:
                print("  -> Stabil! (std dev =", round(std_dev, 5), ")")
                break

        time.sleep(0.5)
    else:
        print("  -> Batas maksimal tercapai, pakai rata-rata 8 pembacaan terakhir")

    recent = readings[-stable_window:]
    avg_compvolt = sum(recent) / len(recent)

    print("  ==> CompVolt rata-rata untuk PPM", ppm, ":", round(avg_compvolt, 4))

    if cal_points:
        last_ppm, last_v = cal_points[-1]
        if ppm > last_ppm and avg_compvolt < last_v:
            print("  !! PERINGATAN: PPM naik tapi voltage turun dari titik sebelumnya.")

    cal_points.append((ppm, avg_compvolt))
    print("  Bilas dengan aqua + keringkan probe sebelum lanjut ke larutan berikutnya")

# ===== HITUNG REGRESI =====
print("\n\n=== HASIL KALIBRASI ===")
for ppm, v in cal_points:
    print("PPM:", ppm, " | CompVolt:", round(v, 4))

n = len(cal_points)
if n < 2:
    print("\nButuh minimal 2 titik kalibrasi!")
else:
    # --- Regresi Linear ---
    sum_x = sum(v for _, v in cal_points)
    sum_y = sum(p for p, _ in cal_points)
    sum_xy = sum(v * p for p, v in cal_points)
    sum_x2 = sum(v * v for _, v in cal_points)

    a_lin = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    b_lin = (sum_y - a_lin * sum_x) / n

    print("\n=== REGRESI LINEAR (TDS = A*V + B) ===")
    print("A =", round(a_lin, 4))
    print("B =", round(b_lin, 4))

    total_error_lin = 0
    print("\n--- Cek akurasi linear ---")
    for ppm, v in cal_points:
        predicted = a_lin * v + b_lin
        error = predicted - ppm
        total_error_lin += abs(error)
        print("PPM asli:", ppm, "| prediksi:", round(predicted, 2), "| Error:", round(error, 2))
    avg_err_lin = total_error_lin / n
    print("Rata-rata error absolut (linear):", round(avg_err_lin, 2), "ppm")

    # --- Regresi Kuadratik (jika n >= 3) ---
    if n >= 3:
        # Solve normal equations untuk y = A*x^2 + B*x + C
        # menggunakan matrix 3x3 manual (Cramer's rule / Gaussian elimination)
        Sx = sum(v for _, v in cal_points)
        Sx2 = sum(v**2 for _, v in cal_points)
        Sx3 = sum(v**3 for _, v in cal_points)
        Sx4 = sum(v**4 for _, v in cal_points)
        Sy = sum(p for p, _ in cal_points)
        Sxy = sum(v*p for p, v in cal_points)
        Sx2y = sum((v**2)*p for p, v in cal_points)

        # Matrix:
        # [Sx4 Sx3 Sx2] [A]   [Sx2y]
        # [Sx3 Sx2 Sx ] [B] = [Sxy ]
        # [Sx2 Sx  n  ] [C]   [Sy  ]

        # Gaussian elimination
        M = [
            [Sx4, Sx3, Sx2, Sx2y],
            [Sx3, Sx2, Sx,  Sxy],
            [Sx2, Sx,  n,   Sy]
        ]

        # Forward elimination
        for i in range(3):
            pivot = M[i][i]
            for j in range(i+1, 3):
                factor = M[j][i] / pivot
                for k in range(4):
                    M[j][k] -= factor * M[i][k]

        # Back substitution
        C = M[2][3] / M[2][2]
        B = (M[1][3] - M[1][2]*C) / M[1][1]
        A = (M[0][3] - M[0][1]*B - M[0][2]*C) / M[0][0]

        print("\n=== REGRESI KUADRATIK (TDS = A*V^2 + B*V + C) ===")
        print("A =", round(A, 4))
        print("B =", round(B, 4))
        print("C =", round(C, 4))

        total_error_quad = 0
        print("\n--- Cek akurasi kuadratik ---")
        for ppm, v in cal_points:
            predicted = A * v**2 + B * v + C
            error = predicted - ppm
            total_error_quad += abs(error)
            print("PPM asli:", ppm, "| prediksi:", round(predicted, 2), "| Error:", round(error, 2))
        avg_err_quad = total_error_quad / n
        print("Rata-rata error absolut (kuadratik):", round(avg_err_quad, 2), "ppm")

        # --- Rekomendasi ---
        print("\n=== REKOMENDASI ===")
        if avg_err_quad < avg_err_lin:
            print("Gunakan KUADRATIK (error lebih kecil)")
            print(">>> CAL_A =", round(A, 6))
            print(">>> CAL_B =", round(B, 6))
            print(">>> CAL_C =", round(C, 6))
            print(">>> CAL_MODE = 'quad'")
        else:
            print("Gunakan LINEAR (error lebih kecil atau sama)")
            print(">>> CAL_A =", round(a_lin, 6))
            print(">>> CAL_B =", round(b_lin, 6))
            print(">>> CAL_MODE = 'linear'")
    else:
        print("\n>>> Simpan nilai ini ke kode final:")
        print("CAL_A =", round(a_lin, 4))
        print("CAL_B =", round(b_lin, 4))
        print("CAL_MODE = 'linear'")
