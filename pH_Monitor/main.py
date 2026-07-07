"""
Water Quality Monitor with pH Sensor
Raspberry Pi Pico 2 (RP2350)
Real-time Smooth Display
"""

import machine
import time
import sys

# Hardware configuration
I2C_ID = 1
SDA_PIN = 6
SCL_PIN = 7
OLED_ADDR = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64

ADC_PIN = 26
ADC_REF = 3.3
ADC_MAX = 65535

# Filter configuration
SAMPLING_INTERVAL_MS = 100
OLED_UPDATE_INTERVAL_MS = 500
SERIAL_INTERVAL_MS = 1000

# Filter yang lebih kuat
MEDIAN_FILTER_SIZE = 10
MOVING_AVERAGE_SIZE = 20
EMA_ALPHA = 0.20

# Calibration points (voltage, pH)
CAL_POINTS = [
    (3.29406, 4.01),
    (2.94870, 6.86),
    (2.52498, 9.18)
]
CAL_POINTS.sort(key=lambda x: x[0])

class pHMonitor:
    def __init__(self):
        print("\nInitializing pH Monitor...")
        
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
            self.adc = machine.ADC(machine.Pin(ADC_PIN))
            print(f"✓ ADC initialized on GP{ADC_PIN}")
        except Exception as e:
            print(f"ADC init failed: {e}")
            raise
        
        # Filter buffers
        self.median_buffer = []
        self.moving_buffer = []
        self.ema_value = None
        
        # Data history untuk rata-rata
        self.ph_history = []
        self.voltage_history = []
        
        # Statistics
        self.raw_ph = 0.0
        self.filtered_ph = 0.0
        self.voltage = 0.0
        self.adc_value = 0
        
        # Display values
        self.display_ph = 7.0
        self.display_voltage = 2.9
        
        # Test ADC
        self.test_adc()
        
        # Show splash screen
        self.show_splash()
    
    def show_splash(self):
        """Tampilkan splash screen"""
        if not self.oled_ok or not self.oled:
            return
        
        try:
            self.oled.fill(0)
            self.oled.rect(0, 0, 128, 64, 1)
            self.oled.text("pH MONITOR", 20, 15, 1)
            self.oled.text("Raspberry Pi Pico 2", 5, 30, 1)
            self.oled.text("Loading...", 30, 45, 1)
            self.oled.show()
            time.sleep(1)
            
            self.oled.fill(0)
            self.oled.rect(0, 0, 128, 64, 1)
            self.oled.text("READY!", 45, 25, 1)
            self.oled.text("Monitoring...", 25, 40, 1)
            self.oled.show()
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Splash error: {e}")
    
    def test_adc(self):
        try:
            raw = self.adc.read_u16()
            voltage = (raw / ADC_MAX) * ADC_REF
            print(f"ADC Test - Raw: {raw}, Voltage: {voltage:.3f}V")
        except Exception as e:
            print(f"ADC test error: {e}")
    
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
    
    def read_adc_voltage(self):
        try:
            raw = self.adc.read_u16()
            self.adc_value = raw
            return (raw / ADC_MAX) * ADC_REF
        except Exception as e:
            print(f"ADC read error: {e}")
            return 0.0
    
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
            return 7.0  # Return neutral pH if error
    
    def get_pH_value(self):
        try:
            # Baca ADC
            self.voltage = self.read_adc_voltage()
            
            # Median filter pada voltage
            filtered_voltage = self.median_filter(self.voltage)
            
            # Hitung pH
            raw_ph = self.calculate_pH(filtered_voltage)
            self.raw_ph = raw_ph
            
            # Moving average
            avg_ph = self.moving_average(raw_ph)
            
            # EMA filter
            filtered_ph = self.ema_filter(avg_ph)
            self.filtered_ph = filtered_ph
            
            # Simpan ke history
            self.ph_history.append(filtered_ph)
            self.voltage_history.append(self.voltage)
            
            if len(self.ph_history) > MOVING_AVERAGE_SIZE:
                self.ph_history.pop(0)
                self.voltage_history.pop(0)
            
            return filtered_ph
        except Exception as e:
            print(f"get_pH error: {e}")
            return self.filtered_ph
    
    def get_average_values(self):
        try:
            if len(self.ph_history) > 0:
                avg_ph = sum(self.ph_history) / len(self.ph_history)
                avg_voltage = sum(self.voltage_history) / len(self.voltage_history)
                return avg_ph, avg_voltage
            else:
                return self.filtered_ph, self.voltage
        except:
            return self.filtered_ph, self.voltage
    
    def get_status(self, ph):
        if ph < 6.5:
            return "ACID"
        elif ph <= 8.5:
            return "NORMAL"
        else:
            return "BASE"
    
    def draw_oled(self):
        if not self.oled_ok or not self.oled:
            return
        
        try:
            # Dapatkan nilai rata-rata
            avg_ph, avg_voltage = self.get_average_values()
            
            # Update display values dengan smoothing
            self.display_ph = (0.7 * self.display_ph) + (0.3 * avg_ph)
            self.display_voltage = (0.7 * self.display_voltage) + (0.3 * avg_voltage)
            
            ph_display = self.display_ph
            volt_display = self.display_voltage
            
            # Clear
            self.oled.fill(0)
            
            # Border
            self.oled.rect(0, 0, 128, 64, 1)
            self.oled.rect(1, 1, 126, 62, 1)
            
            # Title
            self.oled.text("WATER QUALITY", 18, 3, 1)
            self.oled.hline(10, 12, 108, 1)
            
            # pH Value
            self.oled.text("pH", 8, 18, 1)
            ph_str = f"{ph_display:.2f}"
            ph_x = 55 - (len(ph_str) * 4)
            self.oled.text(ph_str, ph_x, 17, 1)
            self.oled.hline(ph_x - 2, 29, len(ph_str) * 8 + 4, 1)
            
            # Voltage
            self.oled.text("Voltage", 8, 34, 1)
            volt_str = f"{volt_display:.3f}V"
            self.oled.text(volt_str, 68, 34, 1)
            
            # Status
            status = self.get_status(ph_display)
            status_y = 48
            
            self.oled.text("Status", 8, status_y, 1)
            
            # Status box
            box_x = 60
            box_y = status_y - 2
            box_w = 58
            box_h = 12
            self.oled.rect(box_x, box_y, box_w, box_h, 1)
            self.oled.rect(box_x + 1, box_y + 1, box_w - 2, box_h - 2, 1)
            
            # Status text
            status_text = status
            text_x = box_x + (box_w - len(status_text) * 8) // 2 + 2
            self.oled.text(status_text, text_x, box_y + 2, 1)
            
            # Status indicator
            self.oled.fill_rect(4, status_y + 2, 6, 6, 1)
            
            # Time
            current_time = time.localtime()
            time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
            self.oled.text(time_str, 75, 57, 1)
            
            # Sample count
            sample_info = f"S:{len(self.ph_history)}"
            self.oled.text(sample_info, 8, 57, 1)
            
            self.oled.show()
            
        except Exception as e:
            print(f"OLED draw error: {e}")
    
    def print_serial(self):
        try:
            avg_ph, avg_voltage = self.get_average_values()
            status = self.get_status(avg_ph)
            print(f"pH: {avg_ph:.2f} | V: {avg_voltage:.4f} | {status} | ADC: {self.adc_value}")
        except Exception as e:
            print(f"Serial print error: {e}")
    
    def run(self):
        print("\n" + "="*50)
        print("pH MONITOR - Raspberry Pi Pico 2")
        print("="*50)
        print(f"OLED: {'✓ Working' if self.oled_ok else '✗ Not available'}")
        print(f"Sampling: {SAMPLING_INTERVAL_MS}ms")
        print(f"Display Update: {OLED_UPDATE_INTERVAL_MS}ms")
        print(f"Moving Average: {MOVING_AVERAGE_SIZE} samples")
        print(f"Median Filter: {MEDIAN_FILTER_SIZE} samples")
        print("\nCalibration points:")
        for v, ph in CAL_POINTS:
            print(f"  {v:.5f}V -> pH {ph:.2f}")
        print("="*50)
        print("Monitoring pH... Press Ctrl+C to stop\n")
        
        last_sample = time.ticks_ms()
        last_oled = time.ticks_ms()
        last_serial = time.ticks_ms()
        
        try:
            while True:
                now = time.ticks_ms()
                
                # Sampling
                if time.ticks_diff(now, last_sample) >= SAMPLING_INTERVAL_MS:
                    self.get_pH_value()
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
        monitor = pHMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.print_exception(e)
        
        # Try to show error on OLED
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
