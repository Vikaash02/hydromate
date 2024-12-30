import RPi.GPIO as GPIO
import spidev  # For ADC like MCP3008
import time
import requests

# GPIO Configuration
motor_pins = {"dir": 16, "step": 18}  # NEMA 17 Stepper Motor Pins
relay_pin = 26  # Relay for water pump
digital_pin = 4  # D0 from soil moisture sensor
adc_channel = 0  # MCP3008 channel for A0 pin (analog output)

# Constants
MOISTURE_THRESHOLD = 500  # Adjust based on calibration
NODE_RED_URL = "http://<Node-RED-IP>:1880/update_data"  # Replace with Node-RED IP

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor Pins Setup
GPIO.setup(motor_pins["dir"], GPIO.OUT)
GPIO.setup(motor_pins["step"], GPIO.OUT)

# Relay Pin Setup
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, GPIO.LOW)  # Ensure pump is off initially

# Soil Moisture Sensor Pins
GPIO.setup(digital_pin, GPIO.IN)

# MCP3008 Setup
spi = spidev.SpiDev()
spi.open(0, 0)  # Open bus 0, device 0
spi.max_speed_hz = 1350000

def read_adc(channel):
    """Read the ADC value from the specified channel."""
    if channel < 0 or channel > 7:
        raise ValueError("ADC channel must be between 0 and 7")
    
    # Send start bit, single-ended bit, and channel bits
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((adc[1] & 3) << 8) + adc[2]
    return value

def check_soil_moisture():
    """Read soil moisture levels from both analog and digital outputs."""
    # Digital Output (D0)
    digital_value = GPIO.input(digital_pin)

    # Analog Output (A0)
    analog_value = read_adc(adc_channel)

    return digital_value, analog_value

def move_motor(steps, direction="down", delay=0.01):
    """Move the motor a specified number of steps."""
    GPIO.output(motor_pins["dir"], GPIO.HIGH if direction == "down" else GPIO.LOW)
    for _ in range(steps):
        GPIO.output(motor_pins["step"], GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(motor_pins["step"], GPIO.LOW)
        time.sleep(delay)

def control_pump(action):
    """Control the water pump."""
    GPIO.output(relay_pin, GPIO.HIGH if action == "on" else GPIO.LOW)

def send_data_to_nodered(moisture, humidity):
    """Send soil moisture and humidity data to Node-RED."""
    data = {"moisture": moisture, "humidity": humidity}
    try:
        requests.post(NODE_RED_URL, json=data)
    except Exception as e:
        print(f"Error sending data to Node-RED: {e}")

# Main Process
def perform_secondary_process():
    print("Starting secondary process...")

    # Move robotic arm down to detect soil moisture
    print("Lowering robotic arm...")
    move_motor(1000, direction="down", delay=0.01)  # Adjust steps and delay as needed

    # Read soil moisture
    print("Detecting soil moisture...")
    digital, analog = check_soil_moisture()
    print(f"Digital Output: {digital} | Analog Value: {analog}")

    # Simulate reading humidity (replace with actual sensor code if available)
    humidity = 60  # Placeholder value
    print(f"Humidity detected: {humidity}")

    # Send data to Node-RED
    print("Sending data to Node-RED...")
    send_data_to_nodered(analog, humidity)

    # Watering logic
    if analog > MOISTURE_THRESHOLD:  # Dry soil detected
        print("Soil moisture below threshold. Activating water pump...")
        control_pump("on")
        time.sleep(5)  # Pump water for 5 seconds
        control_pump("off")
        print("Watering complete.")

    # Move robotic arm back up
    print("Raising robotic arm...")
    move_motor(1000, direction="up", delay=0.01)  # Adjust steps and delay as needed

    print("Secondary process complete.")

# Main Execution
if __name__ == "__main__":
    try:
        perform_secondary_process()
    except KeyboardInterrupt:
        print("Process interrupted.")
    finally:
        control_pump("off")
        spi.close()
        GPIO.cleanup()
