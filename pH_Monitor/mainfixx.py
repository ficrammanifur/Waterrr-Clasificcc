"""
Water Quality Monitor with Classification
Raspberry Pi Pico 2 (RP2350)
Simple OLED Display
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
OLED_UPDATE_INTERVAL_MS = 1000  # Update setiap 1 detik
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

# TDS Calibration
TDS_CAL_FACTOR = 2.8
TDS_TEMP_COEFF = 0.02

# Turbidity Calibration
TURB_JERNIH = 2150
TURB_KERUH = 200
TURB_RANGE = TURB_JERNIH - TURB_KERUH

# ============================================
# WATER CLASSIFIER
# ============================================

class WaterClassifier:
    @staticmethod
    def classify(pH, tds, turb, temp):
        """Klasifikasi air berdasarkan parameter"""
        
        # Hitung skor kelayakan (0-100)
        score = 100.0
        
        # Penalti pH
        if pH < 6.5:
            score -= 30
        elif pH > 9.5:
            score -= 30
        elif pH < 7.0 or pH > 8.5:
            score -= 10
        
        # Penalti TDS
        if tds > 500:
            score -= 40
        elif tds > 300:
            score -= 25
        elif tds > 200:
            score -= 10
        
        # Penalti Turbidity
        if turb > 20:
            score -= 30
        elif turb > 10:
            score -= 20
        elif turb > 5:
            score -= 10
        
        # Penalti Suhu
        if temp > 35 or temp < 10:
            score -= 20
        elif temp > 30:
            score -= 5
        
        # Batasi score
        score = max(0, min(100, score))
        
        # Status
        if score >= 70:
            status = "LAYAK"
            kategori = "AMAN"
        elif score >= 50:
            status = "TIDAK LAYAK"
            kategori = "PERLU OLAH"
        else:
            status = "TIDAK LAYAK"
            kategori = "BAHAYA"
        
        return score, status, kategori

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
        
        # Initialize ADC
        try:
            self.adc_ph = machine.ADC(machine.Pin(ADC_PH_PIN))
            self.adc_tds = machine.ADC(machine.Pin(ADC_TDS_PIN))
            self.adc_turbidity = machine.ADC(machine.Pin(ADC_TURBIDITY_PIN))
            print(f"✓ ADC initialized")
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
                print(f"✓ DS18B20 found")
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
        
        # TDS buffers
        self.tds_median_buffer = []
        self.tds_average_buffer = []
        
        # Sensor values
        self.ph_value = 0.0
        self.ph_voltage = 0.0
        self.tds_value = 0.0
        self.tds_voltage = 0.0
        self.temperature = 0.0
        self.turbidity = 0.0
        self.turbidity_raw = 0
        
        # Display values (smoothed)
        self.display_ph = 7.0
        self.display_tds = 0.0
        self.display_temp = 0.0
        self.display_turb = 0.0
        
        # Classification result
        self.classification = None
        
        # Test sensors
        self.test_sensors()
        
        # Show splash screen
        self.show_splash()
    
    def show_splash(self):
        if not self.oled_ok or not self.oled:
            return
        
        try:
            self.oled.fill(0)
            self.oled.text("pH MONITOR", 20, 20, 1)
            self.oled.text("Loading...", 30, 40, 1)
            self.oled.show()
            time.sleep(1)
            
        except Exception as e:
            print(f"Splash error: {e}")
    
    def test_sensors(self):
        try:
            raw = self.adc_ph.read_u16()
            voltage = (raw / ADC_MAX) * ADC_REF
            print(f"pH Test - Raw: {raw}, Voltage: {voltage:.3f}V")
            
            raw = self.adc_tds.read_u16()
            voltage = (raw / ADC_MAX) * ADC_REF
            print(f"TDS Test - Raw: {raw}, Voltage: {voltage:.3f}V")
            
            raw = self.adc_turbidity.read_u16()
            value = raw >> 4
            print(f"Turbidity Test - Raw: {value}")
            
            if self.ds_ok:
                self.ds_sensor.convert_temp()
                time.sleep(0.75)
                temp = self.ds_sensor.read_temp(self.roms[0])
                print(f"Temperature Test: {temp:.2f}C")
            
        except Exception as e:
            print(f"Sensor test error: {e}")
    
    # ============ PH FUNCTIONS ============
    def median_filter_ph(self, value):
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
    
    def moving_average_ph(self, value):
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
            
            filtered_voltage = self.median_filter_ph(voltage)
            raw_ph = self.calculate_pH(filtered_voltage)
            avg_ph = self.moving_average_ph(raw_ph)
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
    
    # ============ TDS FUNCTIONS ============
    def median_filter_tds(self, value):
        try:
            self.tds_median_buffer.append(value)
            if len(self.tds_median_buffer) > 5:
                self.tds_median_buffer.pop(0)
            
            if len(self.tds_median_buffer) < 5:
                return value
            
            sorted_buffer = sorted(self.tds_median_buffer)
            return sorted_buffer[2]
        except:
            return value
    
    def read_tds(self, temperature):
        try:
            samples = []
            for _ in range(50):
                samples.append(self.adc_tds.read_u16())
                time.sleep_ms(2)
            
            raw_avg = sum(samples) / len(samples)
            voltage = raw_avg * ADC_REF / ADC_MAX
            self.tds_voltage = voltage
            
            filtered_voltage = self.median_filter_tds(voltage)
            
            temp_factor = 1.0 + TDS_TEMP_COEFF * (temperature - 25.0)
            compensated_voltage = filtered_voltage / temp_factor
            
            tds = (compensated_voltage * 1000.0) / TDS_CAL_FACTOR
            
            if tds < 0:
                tds = 0
            elif tds > 5000:
                tds = 5000
            
            self.tds_average_buffer.append(tds)
            if len(self.tds_average_buffer) > 10:
                self.tds_average_buffer.pop(0)
            
            if len(self.tds_average_buffer) > 0:
                tds = sum(self.tds_average_buffer) / len(self.tds_average_buffer)
            
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
            
            if ntu < 0:
                ntu = 0
            elif ntu > 100:
                ntu = 100
            
            self.turbidity = ntu
            return ntu
        except Exception as e:
            print(f"Turbidity read error: {e}")
            return self.turbidity
    
    # ============ CLASSIFICATION ============
    def classify_water(self):
        return WaterClassifier.classify(
            self.ph_value,
            self.tds_value,
            self.turbidity,
            self.temperature
        )
    
    # ============ SIMPLE OLED DISPLAY ============
    def draw_oled(self):
        if not self.oled_ok or not self.oled:
            return
        
        try:
            # Smooth display values
            self.display_ph = (0.7 * self.display_ph) + (0.3 * self.ph_value)
            self.display_tds = (0.7 * self.display_tds) + (0.3 * self.tds_value)
            self.display_temp = (0.7 * self.display_temp) + (0.3 * self.temperature)
            self.display_turb = (0.7 * self.display_turb) + (0.3 * self.turbidity)
            
            # Classify
            score, status, kategori = self.classify_water()
            
            # Clear screen
            self.oled.fill(0)
            
            # === LINE 1: pH | ppm ===
            # pH
            ph_str = f"pH {self.display_ph:.2f}"
            self.oled.text(ph_str, 2, 5, 1)
            
            # Separator
            self.oled.text("|", 72, 5, 1)
            
            # TDS (ppm)
            tds_str = f"ppm {self.display_tds:.0f}"
            self.oled.text(tds_str, 80, 5, 1)
            
            # === LINE 2: STATUS (LAYAK / TIDAK LAYAK) ===
            # Status text centered
            if status == "LAYAK":
                status_x = (128 - len(status) * 8) // 2
                self.oled.text(status, status_x, 25, 1)
                # Draw underline
                self.oled.hline(status_x, 35, len(status) * 8, 1)
            else:
                status_x = (128 - len(status) * 8) // 2
                self.oled.text(status, status_x, 25, 1)
                # Draw underline
                self.oled.hline(status_x, 35, len(status) * 8, 1)
            
            # === LINE 3: Score | Temperature ===
            # Score
            score_str = f"{score:.0f}%"
            self.oled.text(score_str, 2, 45, 1)
            
            # Separator
            self.oled.text("|", 72, 45, 1)
            
            # Temperature
            temp_str = f"{self.display_temp:.1f}C"
            self.oled.text(temp_str, 80, 45, 1)
            
            # Bottom line (thin)
            self.oled.hline(0, 55, 128, 1)
            
            # Small indicator dot for status
            if status == "LAYAK":
                # Green indicator (filled circle)
                self.oled.fill_rect(120, 57, 6, 6, 1)
            else:
                # Red indicator (empty circle with X)
                self.oled.rect(120, 57, 6, 6, 1)
                self.oled.line(121, 58, 125, 62, 1)
                self.oled.line(125, 58, 121, 62, 1)
            
            # Update display
            self.oled.show()
            
        except Exception as e:
            print(f"OLED draw error: {e}")
    
    def print_serial(self):
        """Print data ke serial"""
        score, status, kategori = self.classify_water()
        print(f"pH: {self.ph_value:.2f} | TDS: {self.tds_value:.0f}ppm | "
              f"Temp: {self.temperature:.1f}C | Turb: {self.turbidity:.1f}NTU | "
              f"Status: {status} ({score:.0f}%)")
    
    def run(self):
        print("\n" + "="*50)
        print("WATER QUALITY MONITOR")
        print("="*50)
        print(f"OLED: {'✓ Working' if self.oled_ok else '✗ Not available'}")
        print(f"DS18B20: {'✓ Found' if self.ds_ok else '✗ Not found'}")
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
                    self.oled.text("STOPPED", 30, 25, 1)
                    self.oled.text("Press RESET", 20, 40, 1)
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
                monitor.oled.text("ERROR!", 35, 25, 1)
                error_str = str(e)[:14]
                monitor.oled.text(error_str, 20, 40, 1)
                monitor.oled.show()
        except:
            pass
