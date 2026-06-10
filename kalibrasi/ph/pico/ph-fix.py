# Sensor pH Meter - Raspberry Pi Pico 2
# Pin GPIO 26 (A0)

from machine import ADC, Pin
import time

# ============ PIN DEFINITION ============
PIN_PH = 26  # GPIO 26 (ADC0)

# ============ KALIBRASI pH ============
# Rumus: pH = (voltage x SLOPE) + OFFSET
PH_SLOPE = 3.5
PH_OFFSET = 0.0  # Sesuaikan: celupkan ke buffer pH 7.0, offset = 7.0 - (voltage x 3.5)

# ============ INISIALISASI ADC ============
ph_sensor = ADC(Pin(PIN_PH))

# ============ FILTER SETTINGS ============
HISTORY_SIZE = 10
ph_history = []

def baca_ph():
    """Baca nilai pH dengan filter moving average"""
    # Baca raw ADC (16-bit -> 12-bit dengan shift >>4)
    raw = ph_sensor.read_u16() >> 4
    
    # Moving average
    ph_history.append(raw)
    if len(ph_history) > HISTORY_SIZE:
        ph_history.pop(0)
    
    raw_avg = sum(ph_history) // len(ph_history)
    
    # Konversi ke voltage (0-3.3V)
    voltage = raw_avg * 3.3 / 4095.0
    
    # Konversi ke pH
    ph = (PH_SLOPE * voltage) + PH_OFFSET
    
    # Batasi range 0-14
    if ph < 0:
        ph = 0
    elif ph > 14:
        ph = 14
    
    return ph, raw_avg, voltage

# ============ PROGRAM UTAMA ============
print("\n" + "="*50)
print("   pH METER - Raspberry Pi Pico 2")
print("="*50)
print(f"Rumus: pH = (Voltage x {PH_SLOPE}) + {PH_OFFSET}")
print("="*50)

print("\n🔍 Stabilisasi sensor (5 detik)...")
for i in range(5):
    print(f"   {5-i} detik...")
    time.sleep(1)

print("\n✅ Mulai membaca pH...\n")
print("-"*40)
print(f"{'Raw ADC':>8} | {'Voltage':>8} | {'pH':>6}")
print("-"*40)

while True:
    try:
        ph, raw, voltage = baca_ph()
        
        # Tentukan status
        if ph < 6.5:
            status = "ASAM"
        elif ph > 8.5:
            status = "BASA"
        else:
            status = "NETRAL"
        
        print(f"{raw:8.0f} | {voltage:8.3f}V | {ph:6.2f} | {status}")
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n" + "-"*40)
        print("\n📊 Pembacaan pH dihentikan")
        break
