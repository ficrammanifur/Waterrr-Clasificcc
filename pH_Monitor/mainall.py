"""
Water Quality Monitor with pH, TDS, Temperature, Turbidity
Raspberry Pi Pico 2 (RP2350)
"""

import machine
import time
import sys
import onewire
import ds18x20

# Hardware configuration
I2C_ID = 1
SDA_PIN = 6
SCL_PIN = 7
OLED_ADDR = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64

# Sensor pins
ADC_PH_PIN = 26
ADC_TDS_PIN = 27
ADC_TURBIDITY_PIN = 28
DS18B20_PIN = 16

# ADC configuration
ADC_REF = 3.3
ADC_MAX = 65535

# Filter configuration
SAMPLING_INTERVAL_MS = 100
OLED_UPDATE_INTERVAL_MS = 1000
SERIAL_INTERVAL_MS = 2000

# Filter untuk pH
MEDIAN_FILTER_SIZE = 10
MOVING_AVERAGE_SIZE = 20
EMA_ALPHA = 0.20

# Calibration points pH (voltage, pH)
CAL_POINTS = [
    (3.2487, 4.01),
    (2.94870, 6.86),
    (2.52498, 9.18)
]
CAL_POINTS.sort(key=lambda x: x[0])

# ============ TDS CALIBRATION - DIPERBAIKI ============
# Menggunakan formula yang lebih sederhana dan akurat
# TDS = (Voltage * 1000) / faktor_kalibrasi
# Faktor kalibrasi disesuaikan agar output mendekati 980ppm

TDS_CAL_FACTOR = 2.8  # Faktor kalibrasi - disesuaikan
TDS_TEMP_COEFF = 0.02  # Koefisien suhu

# Turbidity Calibration
TURB_JERNIH = 2150
TURB_KERUH = 200
TURB_RANGE = TURB_JERNIH - TURB_KERUH

class WaterQualityMonitor:
    def __init__(self):
        print("\nInitializing Water Quality Monitor...")
        
        # Initialize I2C
        try:
            self.i2c = machine.I2C(I2C_ID, sda=machine.Pin(SDA_PIN), 
                                   scl=machine.Pin(SCL_PIN), freq=400000)
            devices = self.i2c.scan()
            print(f"I2C devices: {[hex(d) for d in devices]}")
        except Exception as e:
            print(f"I2C error: {e}")
            self.i2c = None
        
        # Initialize OLED
        self.oled = None
        self.oled_ok = False
        
        if self.i2c and OLED_ADDR in self.i2c.scan():
            try:
                from ssd1306 import SSD1306
                self.oled = SSD1306(OLED_WIDTH, OLED_HEIGHT, self.i2c, OLED_ADDR)
                self.oled.contrast(255)
                self.oled_ok = True
                print("✓ OLED initialized and working!")
            except Exception as e:
                print(f"OLED init failed: {e}")
                self.oled = None
                self.oled_ok = False
        else:
            print("✗ OLED not found")
        
        # Initialize ADC sensors
        try:
            self.adc_ph = machine.ADC(machine.Pin(ADC_PH_PIN))
            self.adc_tds = machine.ADC(machine.Pin(ADC_TDS_PIN))
            self.adc_turbidity = machine.ADC(machine.Pin(ADC_TURBIDITY_PIN))
            print(f"✓ ADC initialized - pH:GP{ADC_PH_PIN}, TDS:GP{ADC_TDS_PIN}, Turbidity:GP{ADC_TURBIDITY_PIN}")
        except Exception as e:
            print(f"ADC init failed: {e}")
            raise
        
        # Initialize DS18B20
        self.ds_pin = machine.Pin(DS18B20_PIN)
        self.ds_sensor = None
        self.ds_ok = False
        
        try:
            self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(self.ds_pin))
            self.roms = self.ds_sensor.scan()
            if self.roms:
                self.ds_ok = True
                print(f"✓ DS18B20 found: {self.roms[0]}")
            else:
                print("✗ DS18B20 not found")
        except Exception as e:
            print(f"DS18B20 error: {e}")
        
        # pH Filter buffers
        self.median_buffer = []
        self.moving_buffer = []
        self.ema_value = None
        self.ph_history = []
        self.voltage_history = []
        
        # Sensor values
        self.ph_value = 0.0
        self.ph_voltage = 0.0
        self.tds_value = 0.0
        self.tds_voltage = 0.0
        self.tds_raw_voltage = 0.0
        self.temperature = 0.0
        self.turbidity = 0.0
        self.turbidity_raw = 0
        
        # Display values (smoothed)
        self.display_ph = 7.0
        self.display_tds = 0.0
        self.display_temp = 0.0
        self.display_turb = 0.0
        
        # Test sensors
        self.test_sensors()
        
        # Show splash screen
        self.show_splash()
    
    def show_splash(self):
        """Tampilkan splash screen"""
        if not self.oled_ok or not self.oled:
            return
        
        try:
            self.oled.fill(0)
            self.oled.rect(0, 0, 128, 64, 1)
            self.oled.text("WATER QUALITY", 10, 10, 1)
            self.oled.text("MONITOR", 30, 22, 1)
            self.oled.text("Raspberry Pi Pico 2", 5, 38, 1)
            self.oled.text("Loading...", 30, 50, 1)
            self.oled.show()
            time.sleep(1.5)
            
        except Exception as e:
            print(f"Splash error: {e}")
    
    def test_sensors(self):
        """Test semua sensor"""
        try:
            # Test pH
            raw = self.adc_ph.read_u16()
            voltage = (raw / ADC_MAX) * ADC_REF
            print(f"pH ADC Test - Raw: {raw}, Voltage: {voltage:.3f}V")
            
            # Test TDS
            raw = self.adc_tds.read_u16()
            voltage = (raw / ADC_MAX) * ADC_REF
            print(f"TDS ADC Test - Raw: {raw}, Voltage: {voltage:.3f}V")
            
            # Test Turbidity
            raw = self.adc_turbidity.read_u16()
            value = raw >> 4
            voltage = value * 3.3 / 4095.0
            print(f"Turbidity Test - Raw: {value}, Voltage: {voltage:.2f}V")
            
            # Test DS18B20
            if self.ds_ok:
                self.ds_sensor.convert_temp()
                time.sleep(0.75)
                temp = self.ds_sensor.read_temp(self.roms[0])
                print(f"Temperature Test: {temp:.2f}°C")
            
        except Exception as e:
            print(f"Sensor test error: {e}")
    
    # ============ PH FUNCTIONS ============
    def median_filter(self, value):
        try:
            self.median_buffer.append(value)
            if len(self.median_buffer) > MEDIAN_FILTER_SIZE:
                self.median_buffer.pop(0)
            
            if len(self.median_buffer) < MEDIAN_FILTER_SIZE:
                return value
            
            sorted_buffer = sorted(self.median_buffer)
            return sorted_buffer[MEDIAN_FILTER_SIZE // 2]
        except:
            return value
    
    def moving_average(self, value):
        try:
            self.moving_buffer.append(value)
            if len(self.moving_buffer) > MOVING_AVERAGE_SIZE:
                self.moving_buffer.pop(0)
            return sum(self.moving_buffer) / len(self.moving_buffer)
        except:
            return value
    
    def ema_filter(self, value):
        try:
            if self.ema_value is None:
                self.ema_value = value
            else:
                self.ema_value = EMA_ALPHA * value + (1 - EMA_ALPHA) * self.ema_value
            return self.ema_value
        except:
            return value
    
    def calculate_pH(self, voltage):
        try:
            if voltage <= CAL_POINTS[0][0]:
                v1, ph1 = CAL_POINTS[0]
                v2, ph2 = CAL_POINTS[1]
                slope = (ph2 - ph1) / (v2 - v1) if (v2 - v1) != 0 else 0
                return ph1 + slope * (voltage - v1)
            
            if voltage >= CAL_POINTS[-1][0]:
                v1, ph1 = CAL_POINTS[-2]
                v2, ph2 = CAL_POINTS[-1]
                slope = (ph2 - ph1) / (v2 - v1) if (v2 - v1) != 0 else 0
                return ph1 + slope * (voltage - v1)
            
            for i in range(len(CAL_POINTS) - 1):
                v1, ph1 = CAL_POINTS[i]
                v2, ph2 = CAL_POINTS[i + 1]
                if v1 <= voltage <= v2:
                    if v2 - v1 == 0:
                        return ph1
                    t = (voltage - v1) / (v2 - v1)
                    return ph1 + t * (ph2 - ph1)
            
            return CAL_POINTS[1][1]
        except:
            return 7.0
    
    def read_ph(self):
        try:
            raw = self.adc_ph.read_u16()
            voltage = (raw / ADC_MAX) * ADC_REF
            self.ph_voltage = voltage
            
            filtered_voltage = self.median_filter(voltage)
            raw_ph = self.calculate_pH(filtered_voltage)
            avg_ph = self.moving_average(raw_ph)
            filtered_ph = self.ema_filter(avg_ph)
            
            self.ph_history.append(filtered_ph)
            self.voltage_history.append(voltage)
            
            if len(self.ph_history) > MOVING_AVERAGE_SIZE:
                self.ph_history.pop(0)
                self.voltage_history.pop(0)
            
            self.ph_value = filtered_ph
            return filtered_ph
        except Exception as e:
            print(f"pH read error: {e}")
            return self.ph_value
    
    # ============ TDS FUNCTIONS - DIPERBAIKI ============
    def read_tds(self, temperature):
        try:
            # Baca 50 sample untuk rata-rata
            samples = []
            for _ in range(50):
                samples.append(self.adc_tds.read_u16())
                time.sleep(0.01)
            
            raw = sum(samples) / len(samples)
            voltage = raw * 3.3 / ADC_MAX
            self.tds_raw_voltage = voltage
            
            # Kompensasi suhu (25°C reference)
            temp_factor = 1.0 + TDS_TEMP_COEFF * (temperature - 25.0)
            compensated_voltage = voltage / temp_factor
            
            # Konversi ke TDS menggunakan faktor kalibrasi yang disesuaikan
            # TDS (ppm) = (Voltage * 1000) / Faktor
            # Faktor disesuaikan agar output = 980ppm
            tds = (compensated_voltage * 1000.0) / TDS_CAL_FACTOR
            
            # Batasi nilai minimum dan maksimum
            if tds < 0:
                tds = 0
            elif tds > 5000:
                tds = 5000  # Batasi maksimum 5000ppm
            
            self.tds_value = tds
            return tds
            
        except Exception as e:
            print(f"TDS read error: {e}")
            return self.tds_value
    
    # ============ TEMPERATURE FUNCTIONS ============
    def read_temperature(self):
        try:
            if not self.ds_ok:
                return 25.0
            
            self.ds_sensor.convert_temp()
            time.sleep(0.75)
            temp = self.ds_sensor.read_temp(self.roms[0])
            self.temperature = temp
            return temp
        except Exception as e:
            print(f"Temperature read error: {e}")
            return self.temperature
    
    # ============ TURBIDITY FUNCTIONS ============
    def read_turbidity(self):
        try:
            raw_16bit = self.adc_turbidity.read_u16()
            nilai = raw_16bit >> 4
            self.turbidity_raw = nilai
            
            if nilai >= TURB_JERNIH:
                ntu = 0.0
            elif nilai <= TURB_KERUH:
                ntu = 100.0
            else:
                ntu = (TURB_JERNIH - nilai) * 100.0 / TURB_RANGE
            
            # Batasi nilai
            if ntu < 0:
                ntu = 0
            elif ntu > 100:
                ntu = 100
            
            self.turbidity = ntu
            return ntu
        except Exception as e:
            print(f"Turbidity read error: {e}")
            return self.turbidity
    
    # ============ DISPLAY FUNCTIONS ============
    def get_status(self, ph):
        if ph < 6.5:
            return "ACID"
        elif ph <= 8.5:
            return "NORMAL"
        else:
            return "BASE"
    
    def get_water_quality(self, turb):
        if turb < 5:
            return "JERNIH"
        elif turb < 20:
            return "AGAK"
        elif turb < 50:
            return "KERUH"
        else:
            return "KOTOR"
    
    def draw_oled(self):
        if not self.oled_ok or not self.oled:
            return
        
        try:
            # Smooth display values
            self.display_ph = (0.7 * self.display_ph) + (0.3 * self.ph_value)
            self.display_tds = (0.7 * self.display_tds) + (0.3 * self.tds_value)
            self.display_temp = (0.7 * self.display_temp) + (0.3 * self.temperature)
            self.display_turb = (0.7 * self.display_turb) + (0.3 * self.turbidity)
            
            self.oled.fill(0)
            
            # Border
            self.oled.rect(0, 0, 128, 64, 1)
            self.oled.rect(1, 1, 126, 62, 1)
            
            # Title
            self.oled.text("WATER QUALITY", 18, 2, 1)
            self.oled.hline(10, 11, 108, 1)
            
            # pH (Baris 1)
            self.oled.text("pH", 3, 15, 1)
            ph_str = f"{self.display_ph:.2f}"
            self.oled.text(ph_str, 35, 15, 1)
            
            # Status pH
            status = self.get_status(self.display_ph)
            self.oled.text(status, 80, 15, 1)
            
            # TDS (Baris 2)
            self.oled.text("TDS", 3, 26, 1)
            tds_str = f"{self.display_tds:.0f}ppm"
            self.oled.text(tds_str, 35, 26, 1)
            
            # Temperature (Baris 3)
            self.oled.text("Temp", 3, 37, 1)
            temp_str = f"{self.display_temp:.1f}C"
            self.oled.text(temp_str, 35, 37, 1)
            
            # Turbidity (Baris 4)
            self.oled.text("Turb", 3, 48, 1)
            turb_str = f"{self.display_turb:.1f}NTU"
            self.oled.text(turb_str, 35, 48, 1)
            
            # Vertical separator
            self.oled.vline(72, 14, 46, 1)
            
            # Water quality indicator (right side)
            quality = self.get_water_quality(self.display_turb)
            self.oled.text("QUALITY", 78, 18, 1)
            self.oled.text(quality, 80, 30, 1)
            
            # Simple bar indicator for quality
            bar_x = 78
            bar_y = 42
            bar_w = 44
            bar_h = 12
            
            # Draw bar border
            self.oled.rect(bar_x, bar_y, bar_w, bar_h, 1)
            
            # Fill bar based on turbidity
            if self.display_turb < 5:
                # JERNIH - isi penuh
                self.oled.fill_rect(bar_x + 1, bar_y + 1, bar_w - 2, bar_h - 2, 1)
            elif self.display_turb < 20:
                # AGAK - isi 75%
                fill_w = int((bar_w - 2) * 0.75)
                self.oled.fill_rect(bar_x + 1, bar_y + 1, fill_w, bar_h - 2, 1)
            elif self.display_turb < 50:
                # KERUH - isi 40%
                fill_w = int((bar_w - 2) * 0.40)
                self.oled.fill_rect(bar_x + 1, bar_y + 1, fill_w, bar_h - 2, 1)
            else:
                # KOTOR - isi 10%
                fill_w = int((bar_w - 2) * 0.10)
                self.oled.fill_rect(bar_x + 1, bar_y + 1, fill_w, bar_h - 2, 1)
            
            # Bottom time
            current_time = time.localtime()
            time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
            self.oled.text(time_str, 2, 57, 1)
            
            self.oled.show()
            
        except Exception as e:
            print(f"OLED draw error: {e}")
    
    def print_serial(self):
        """Print semua data ke serial"""
        status = self.get_status(self.ph_value)
        quality = self.get_water_quality(self.turbidity)
        print(f"pH: {self.ph_value:.2f} | TDS: {self.tds_value:.0f}ppm | "
              f"Temp: {self.temperature:.1f}C | Turb: {self.turbidity:.1f}NTU | "
              f"{status} | {quality}")
    
    def run(self):
        print("\n" + "="*50)
        print("WATER QUALITY MONITOR - Raspberry Pi Pico 2")
        print("="*50)
        print(f"OLED: {'✓ Working' if self.oled_ok else '✗ Not available'}")
        print(f"DS18B20: {'✓ Found' if self.ds_ok else '✗ Not found'}")
        print(f"Sampling: {SAMPLING_INTERVAL_MS}ms")
        print(f"Display Update: {OLED_UPDATE_INTERVAL_MS}ms")
        print(f"TDS Calibration Factor: {TDS_CAL_FACTOR}")
        print("\nCalibration points pH:")
        for v, ph in CAL_POINTS:
            print(f"  {v:.5f}V -> pH {ph:.2f}")
        print("="*50)
        print("Monitoring... Press Ctrl+C to stop\n")
        
        last_sample = time.ticks_ms()
        last_oled = time.ticks_ms()
        last_serial = time.ticks_ms()
        
        try:
            while True:
                now = time.ticks_ms()
                
                # Sampling
                if time.ticks_diff(now, last_sample) >= SAMPLING_INTERVAL_MS:
                    temp = self.read_temperature()
                    self.read_ph()
                    self.read_tds(temp)
                    self.read_turbidity()
                    last_sample = now
                
                # Serial print
                if time.ticks_diff(now, last_serial) >= SERIAL_INTERVAL_MS:
                    self.print_serial()
                    last_serial = now
                
                # OLED update
                if time.ticks_diff(now, last_oled) >= OLED_UPDATE_INTERVAL_MS:
                    self.draw_oled()
                    last_oled = now
                
                time.sleep_ms(10)
                
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            if self.oled_ok and self.oled:
                try:
                    self.oled.fill(0)
                    self.oled.rect(0, 0, 128, 64, 1)
                    self.oled.text("MONITOR", 30, 15, 1)
                    self.oled.text("STOPPED", 30, 30, 1)
                    self.oled.text("Press RESET", 20, 45, 1)
                    self.oled.show()
                except:
                    pass
            raise

# Main
if __name__ == "__main__":
    try:
        monitor = WaterQualityMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.print_exception(e)
        
        try:
            if 'monitor' in locals() and monitor.oled_ok:
                monitor.oled.fill(0)
                monitor.oled.rect(0, 0, 128, 64, 1)
                monitor.oled.text("ERROR!", 35, 20, 1)
                error_str = str(e)[:14]
                monitor.oled.text(error_str, 20, 35, 1)
                monitor.oled.show()
        except:
            pass
