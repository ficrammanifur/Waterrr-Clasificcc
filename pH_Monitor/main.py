"""
Water Quality Monitor with pH Sensor
Raspberry Pi Pico 2 (RP2350)
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
SAMPLING_INTERVAL_MS = 20
OLED_UPDATE_INTERVAL_MS = 200
MEDIAN_FILTER_SIZE = 5
MOVING_AVERAGE_SIZE = 10
EMA_ALPHA = 0.35

# Calibration points
CAL_POINTS = [
    (3.29406, 4.01),
    (2.94870, 6.86),
    (2.62498, 9.18)
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
                
                # Show test pattern
                print("Showing test pattern...")
                self.oled.test_pattern()
                time.sleep(2)
                
                # Set max contrast
                self.oled.contrast(255)
                
                self.oled_ok = True
                print("✓ OLED initialized and working!")
                
            except Exception as e:
                print(f"OLED init failed: {e}")
                self.oled = None
                self.oled_ok = False
        else:
            print("✗ OLED not found on I2C bus")
        
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
        
        # Statistics
        self.raw_ph = 0.0
        self.filtered_ph = 0.0
        self.voltage = 0.0
        self.adc_value = 0
        
        # Test ADC
        self.test_adc()
    
    def test_adc(self):
        raw = self.adc.read_u16()
        voltage = (raw / ADC_MAX) * ADC_REF
        print(f"ADC Test - Raw: {raw}, Voltage: {voltage:.3f}V")
    
    def median_filter(self, value):
        self.median_buffer.append(value)
        if len(self.median_buffer) > MEDIAN_FILTER_SIZE:
            self.median_buffer.pop(0)
        if len(self.median_buffer) < MEDIAN_FILTER_SIZE:
            return value
        sorted_buffer = sorted(self.median_buffer)
        return sorted_buffer[MEDIAN_FILTER_SIZE // 2]
    
    def moving_average(self, value):
        self.moving_buffer.append(value)
        if len(self.moving_buffer) > MOVING_AVERAGE_SIZE:
            self.moving_buffer.pop(0)
        return sum(self.moving_buffer) / len(self.moving_buffer)
    
    def ema_filter(self, value):
        if self.ema_value is None:
            self.ema_value = value
        else:
            self.ema_value = EMA_ALPHA * value + (1 - EMA_ALPHA) * self.ema_value
        return self.ema_value
    
    def read_adc_voltage(self):
        raw = self.adc.read_u16()
        self.adc_value = raw
        return (raw / ADC_MAX) * ADC_REF
    
    def calculate_pH(self, voltage):
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
    
    def get_pH_value(self):
        self.voltage = self.read_adc_voltage()
        filtered_voltage = self.median_filter(self.voltage)
        raw_ph = self.calculate_pH(filtered_voltage)
        self.raw_ph = raw_ph
        avg_ph = self.moving_average(raw_ph)
        filtered_ph = self.ema_filter(avg_ph)
        self.filtered_ph = filtered_ph
        return filtered_ph
    
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
            self.oled.fill(0)
            
            # Draw border
            self.oled.rect(0, 0, 128, 64, 1)
            
            # Title with underline
            self.oled.text("pH MONITOR", 28, 2, 1)
            self.oled.hline(0, 12, 128, 1)
            
            # pH value - large and centered
            self.oled.text("pH:", 5, 18, 1)
            ph_str = f"{self.filtered_ph:.2f}"
            # Center the pH value
            ph_x = 60 - (len(ph_str) * 4)
            self.oled.text(ph_str, ph_x, 18, 1)
            
            # Voltage
            self.oled.text("V:", 5, 32, 1)
            self.oled.text(f"{self.voltage:.3f}V", 45, 32, 1)
            
            # Status with box
            status = self.get_status(self.filtered_ph)
            self.oled.text("Status:", 5, 46, 1)
            
            # Status box
            box_x = 60
            box_y = 43
            box_w = 60
            box_h = 12
            
            # Draw box
            self.oled.rect(box_x, box_y, box_w, box_h, 1)
            
            # Fill box based on status
            if status == "ACID":
                # Fill with pattern (drawing lines instead of fill to save memory)
                self.oled.rect(box_x + 1, box_y + 1, box_w - 2, box_h - 2, 1)
            elif status == "NORMAL":
                self.oled.rect(box_x + 1, box_y + 1, box_w - 2, box_h - 2, 1)
            else:  # BASE
                self.oled.rect(box_x + 1, box_y + 1, box_w - 2, box_h - 2, 1)
            
            # Status text
            self.oled.text(status, box_x + 5, box_y + 2, 1)
            
            # Bottom line
            self.oled.hline(0, 63, 128, 1)
            
            # Show
            self.oled.show()
            
        except Exception as e:
            print(f"OLED draw error: {e}")
    
    def print_serial(self):
        status = self.get_status(self.filtered_ph)
        print(f"ADC:{self.adc_value:5d} V:{self.voltage:.4f} "
              f"Raw:{self.raw_ph:.2f} pH:{self.filtered_ph:.2f} [{status}]")
    
    def run(self):
        print("\n=== pH Monitor Started ===")
        print(f"OLED: {'✓ Working' if self.oled_ok else '✗ Not available'}")
        print(f"Sampling: {SAMPLING_INTERVAL_MS}ms")
        print(f"OLED update: {OLED_UPDATE_INTERVAL_MS}ms")
        print("\nCalibration points:")
        for v, ph in CAL_POINTS:
            print(f"  {v:.5f}V -> pH {ph:.2f}")
        print("\n" + "="*40)
        print("Press Ctrl+C to stop\n")
        
        last_sample = time.ticks_ms()
        last_oled = time.ticks_ms()
        sample_count = 0
        
        while True:
            now = time.ticks_ms()
            
            if time.ticks_diff(now, last_sample) >= SAMPLING_INTERVAL_MS:
                self.get_pH_value()
                self.print_serial()
                last_sample = now
                sample_count += 1
            
            if time.ticks_diff(now, last_oled) >= OLED_UPDATE_INTERVAL_MS:
                self.draw_oled()
                last_oled = now
            
            time.sleep_ms(1)

# Main
if __name__ == "__main__":
    try:
        monitor = pHMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\n\n=== Stopped by user ===")
        if monitor.oled_ok:
            try:
                monitor.oled.fill(0)
                monitor.oled.text("STOPPED", 30, 20, 1)
                monitor.oled.text("Press RESET", 20, 35, 1)
                monitor.oled.show()
            except:
                pass
    except Exception as e:
        print(f"\nError: {e}")
        sys.print_exception(e)
