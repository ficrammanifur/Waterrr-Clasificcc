# Turbidity Meter dalam NTU - Rekalibrasi
from machine import ADC, Pin
import time

PIN_TURBIDITY = 28
turb_sensor = ADC(Pin(PIN_TURBIDITY))

# Kalibrasi berdasarkan data Anda
NILAI_JERNIH = 2150    # Nilai tertinggi (air jernih) -> 0 NTU
NILAI_KERUH = 200      # Nilai terendah (sangat keruh) -> 100 NTU
RANGE_NILAI = NILAI_JERNIH - NILAI_KERUH

def baca_ntu():
    raw_16bit = turb_sensor.read_u16()
    nilai = raw_16bit >> 4
    
    if nilai >= NILAI_JERNIH:
        ntu = 0.0
    elif nilai <= NILAI_KERUH:
        ntu = 100.0
    else:
        ntu = (NILAI_JERNIH - nilai) * 100.0 / RANGE_NILAI
    
    tegangan = nilai * 3.3 / 4095.0
    return nilai, tegangan, ntu

print("\n=== TURBIDITY METER (NTU) - REKALIBRASI ===")
print(f"Range: {NILAI_JERNIH} ADC = 0 NTU, {NILAI_KERUH} ADC = 100 NTU\n")

while True:
    try:
        nilai, tegangan, ntu = baca_ntu()
        
        if ntu <= 1:
            status = "SANGAT JERNIH"
        elif ntu <= 5:
            status = "JERNIH"
        elif ntu <= 20:
            status = "AGAK KERUH"
        elif ntu <= 50:
            status = "KERUH"
        else:
            status = "SANGAT KERUH"
        
        print(f"ADC: {nilai:4d} | Volt: {tegangan:.2f}V | NTU: {ntu:5.1f} | {status}")
        time.sleep(0.5)
        
    except KeyboardInterrupt:
        print("\nSelesai")
        break
