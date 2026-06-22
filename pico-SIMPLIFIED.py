# ==========================================
# main.py - VERSI SIMPLIFIED (FOKUS KELAYAKAN)
# ==========================================

import time
import machine
from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C

# ==========================================
# KONFIGURASI HARDWARE
# ==========================================

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

adc_ph = ADC(Pin(26))
adc_tds = ADC(Pin(27))
adc_turb = ADC(Pin(28))
adc_temp = ADC(Pin(29))

led = Pin(25, Pin.OUT)

# ==========================================
# FUNGSI BACA SENSOR
# ==========================================

def read_sensors():
    volt_ph = (adc_ph.read_u16() / 65535) * 3.3
    volt_tds = (adc_tds.read_u16() / 65535) * 3.3
    volt_turb = (adc_turb.read_u16() / 65535) * 3.3
    volt_temp = (adc_temp.read_u16() / 65535) * 3.3
    
    suhu = 25 + (volt_temp - 0.5) * 20
    comp_volt_tds = volt_tds * 0.95
    
    return [volt_ph, comp_volt_tds, volt_turb, suhu]

# ==========================================
# TAMPILAN OLED - FOKUS pH, TDS, KELAYAKAN
# ==========================================

def display_result(ph, tds, kelayakan, confidence):
    oled.fill(0)
    
    # Baris 1: pH
    oled.text(f"pH : {ph:.2f}", 0, 0, 1)
    
    # Baris 2: TDS
    oled.text(f"TDS: {tds:.0f} ppm", 0, 16, 1)
    
    # Baris 3: Status (LAYAK/TIDAK LAYAK)
    if kelayakan == "LAYAK":
        oled.text("STATUS: LAYAK", 0, 32, 1)
    else:
        oled.text("STATUS: TIDAK LAYAK", 0, 32, 1)
    
    # Baris 4: Confidence
    oled.text(f"Conf: {confidence:.1%}", 0, 48, 1)
    
    oled.show()

# ==========================================
# PROGRAM UTAMA
# ==========================================

print("="*40)
print("🌊 SISTEM MONITORING KUALITAS AIR")
print("="*40)

while True:
    try:
        # Baca sensor
        sensor = read_sensors()
        
        # SIMULASI PREDIKSI (ganti dengan model AI nanti)
        # Untuk sekarang, langsung pakai nilai dari sensor
        ph = sensor[0] * 3.2  # Simulasi kalibrasi
        tds = sensor[1] * 500  # Simulasi kalibrasi
        
        # Logika kelayakan sederhana
        if 6.5 <= ph <= 8.5 and tds <= 500:
            kelayakan = "LAYAK"
            confidence = 0.95
        else:
            kelayakan = "TIDAK LAYAK"
            confidence = 0.98
        
        # Tampilkan di OLED
        display_result(ph, tds, kelayakan, confidence)
        
        # Print di terminal
        print("-"*40)
        print(f"pH : {ph:.2f}")
        print(f"TDS: {tds:.0f} ppm")
        print(f"Status: {kelayakan} (Conf: {confidence:.1%})")
        print("-"*40)
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("🔴 Program dihentikan")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(1)
