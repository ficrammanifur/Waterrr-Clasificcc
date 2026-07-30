from machine import Pin, ADC
import utime

# ---- Konfigurasi ADC ----
tds_pin = ADC(Pin(27))
VREF = 3.3
ADC_RESOLUTION = 65535.0

# ---- Buffer averaging ----
AVG_SAMPLES = 30
tds_adc_buf = [0] * AVG_SAMPLES
tds_idx = 0

# =========================================================
# KALIBRASI LINEAR — GANTI SESUAI HASIL KALIBRASI SENSOR KAMU
# =========================================================
V_ZERO = 0.798      # tegangan saat probe di udara / TDS = 0 ppm
V_REF  = 0.928       # tegangan saat probe di larutan referensi
TDS_REF = 180.0      # nilai TDS asli larutan referensi (dari tester)

K = TDS_REF / (V_REF - V_ZERO)   # slope kalibrasi (ppm per volt)

def baca_tds():
    global tds_idx

    adc_value = tds_pin.read_u16()
    tds_adc_buf[tds_idx] = adc_value
    tds_idx = (tds_idx + 1) % AVG_SAMPLES

    avg_adc = sum(tds_adc_buf) / AVG_SAMPLES
    voltage = avg_adc * (VREF / ADC_RESOLUTION)

    tds = (voltage - V_ZERO) * K
    if tds < 0:
        tds = 0

    return avg_adc, voltage, tds

# ---- Isi buffer awal ----
for _ in range(AVG_SAMPLES):
    tds_pin.read_u16()
    utime.sleep_ms(5)

while True:
    avg_adc, voltage, tds = baca_tds()

    print("--------------------------------")
    print("ADC       : {:.0f}".format(avg_adc))
    print("Voltage   : {:.3f} V".format(voltage))
    print("TDS       : {:.1f} ppm".format(tds))

    utime.sleep_ms(200)
