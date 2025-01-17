import RPi.GPIO as GPIO
import time
import importlib

# For NodeRED interface
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

# GPIO Pin Configuration for Motors
motor_pins = {
    "left_motor": {"A": 6, "B": 26},  # Pins for left motor
    "right_motor": {"A": 22, "B": 5},  # Pins for right motor
}

# GPIO Pin Configuration for IR Sensors
LEFT_IR_SENSOR_PIN = 17
RIGHT_IR_SENSOR_PIN = 27

# GPIO Pin Configuration for Stepper Motor
PUL_PIN = 23  # Pulse Pin
DIR_PIN = 24  # Direction Pin
ENA_PIN = 16  # Enable Pin

# GPIO Pin Configuration for Water Pump
RELAY_PIN = 21 

# GPIO Pin Configuration for Soil Moisture Sensor
SOIL_PIN = 7

# GPIO Pin Configuration for Ultrasonic Sensor
TRIG = 13
ECHO = 1

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup Motor Pins
for motor, pins in motor_pins.items():
    GPIO.setup(pins["A"], GPIO.OUT)
    GPIO.setup(pins["B"], GPIO.OUT)

# Setup IR Sensor Pins
GPIO.setup(LEFT_IR_SENSOR_PIN, GPIO.IN)
GPIO.setup(RIGHT_IR_SENSOR_PIN, GPIO.IN)

# Setup Stepper Motor Pins
GPIO.setup(PUL_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(ENA_PIN, GPIO.OUT)

# Setup Water Pump Pins
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Setup Soil Moisture Sensor Pins
GPIO.setup(SOIL_PIN, GPIO.IN)

# Setup Ultrasonic Sensor Pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Enable the stepper driver
GPIO.output(ENA_PIN, GPIO.LOW) # LOW to enable, HIGH to disable

# Increase speed by reducing the pulse delay
pulse_delay = 0.001  # Adjust this value for faster or slower rotation (lower = faster)

data = {
    "ir_status": "",
    "checkpoint": 0,
    "motor_dir": "",
    "water_level": 0,
    "soil_moisture": 0
}

# Create PWM Objects
pwm_controls = {}
for motor, pins in motor_pins.items():
    pwm_controls[motor] = GPIO.PWM(pins["A"], 100)  # 100 Hz frequency
    pwm_controls[motor].start(0)  # Start with 0% duty cycle

# Motor Control Functions
def set_motor(motor, speed):
    """
    Controls motor direction and speed using PWM.
    - speed: Positive for forward, negative for backward, 0 to stop
    """
    pins = motor_pins[motor]
    if speed > 0:  # Forward
        GPIO.output(pins["B"], GPIO.LOW)  # Set B pin LOW
        pwm_controls[motor].ChangeDutyCycle(abs(speed))  # Set PWM duty cycle
    elif speed < 0:  # Backward
        GPIO.output(pins["B"], GPIO.HIGH)  # Set B pin HIGH
        pwm_controls[motor].ChangeDutyCycle(abs(speed))  # Set PWM duty cycle
    else:  # Stop
        GPIO.output(pins["B"], GPIO.LOW)  # Stop motor
        pwm_controls[motor].ChangeDutyCycle(0)  # Set PWM to 0%

def stop_motors():
    """Stops all motors."""
    for motor in motor_pins:
        set_motor(motor, 0)

# Function to rotate motor for a specified time and direction
def rotate_motor(direction, duration):
    GPIO.output(DIR_PIN, direction)  # Set motor direction
    steps = int(duration / pulse_delay)  # Calculate the number of steps based on the duration

    for _ in range(steps):
        GPIO.output(PUL_PIN, GPIO.HIGH)  # Generate pulse
        time.sleep(pulse_delay)
        GPIO.output(PUL_PIN, GPIO.LOW)  # End pulse
        time.sleep(pulse_delay)

# Function to activate the water pump
def activate_pump():
    print("Activating water pump...")
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn on water pump (relay closes)

# Function to deactivate the water pump
def deactivate_pump():
    print("Deactivating water pump...")
    GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn off water pump (relay opens)

# Function to automate watering
def run_water_pump_process():
    stop_count = 0  # Counter for 5-second stops
    deactivate_pump()  # Ensure pump is off initially

    # Rotate for 2.5 seconds clockwise
    print("Rotating clockwise for 2.5 seconds...")
    rotate_motor(GPIO.HIGH, 1.2)  # Clockwise rotation for 2.5 seconds

    # Stop for 5 seconds after clockwise rotation
    print("Stopping for 5 seconds...")
    time.sleep(5)  # Stop for 5 seconds
    read_soil_moisture()  # Read soil moisture
    print(f"Soil Moisture Percentage: {data['soil_moisture']}%")  # Debug output
    stop_count += 1

    # Rotate for 2.5 seconds counter-clockwise
    print("Rotating counter-clockwise for 2.5 seconds...")
    rotate_motor(GPIO.LOW, 1.2)  # Counter-clockwise rotation for 2.5 seconds

    # Stop and check moisture level after second rotation
    stop_count += 1
    if stop_count == 2:
        if data["soil_moisture"] < 30:  # Threshold for low soil moisture (adjust as needed)
            print("Soil moisture is low. Activating water pump...")
            activate_pump()  # Activate water pump
            time.sleep(5)  # Keep the pump on for 5 seconds
            deactivate_pump()  # Deactivate the pump after 5 seconds
            stop_count = 0  # Reset stop counter after pump activation
        else:
            print("Soil moisture is sufficient. No need to activate the water pump.")
            stop_count = 0


# Function for reading water level
def read_water_level():
    """
    Reads the water level using an ultrasonic sensor and calculates the remaining level as a percentage.
    """
    # Trigger the ultrasonic sensor
    GPIO.output(TRIG, False)
    time.sleep(0.1)  # Short delay to ensure stability

    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # Send a 10µs pulse
    GPIO.output(TRIG, False)

    try:
        # Measure the echo response time
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        # Calculate the distance based on the pulse duration
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # Convert to cm

        # Define the tank's distance range
        max_distance = 100.0  # Distance when the tank is empty (adjust to your setup)
        min_distance = 10.0   # Distance when the tank is full (adjust to your setup)

        # Clamp the distance to avoid invalid readings
        clamped_distance = max(min_distance, min(max_distance, distance))

        # Calculate the water level as a percentage
        percentage = ((max_distance - clamped_distance) / (max_distance - min_distance)) * 100
        percentage = max(0, min(100, percentage))  # Ensure percentage stays between 0% and 100%

        # Update the data dictionary with the calculated water level
        data["water_level"] = round(percentage, 2)

        # Print the water level percentage for debugging
        print(f"Water Level: {data['water_level']}%")

    except Exception as e:
        # Handle errors (e.g., sensor timeout or invalid readings)
        print(f"Error reading ultrasonic sensor: {e}")
        data["water_level"] = -1  # Indicate an error with a negative value


# Function for reading soil moisture
def read_soil_moisture():
    wet_time = 0
    dry_time = 0
    start_time = time.time()
    
    # Define the duration for reading soil moisture (e.g., 1 second)
    read_duration = 1.0
    end_time = start_time + read_duration

    # Continuously read the soil sensor state during the read duration
    while time.time() < end_time:
        state = GPIO.input(SOIL_PIN)  # Read the current state (0 = wet, 1 = dry)
        
        current_time = time.time()
        if state == 0:  # Wet state
            wet_time += current_time - start_time
        else:  # Dry state
            dry_time += current_time - start_time
        
        # Update the start time for the next loop
        start_time = current_time

    # Calculate the total time
    total_time = wet_time + dry_time

    # Calculate the moisture percentage (wet time as a percentage of total time)
    if total_time > 0:
        moisture_percentage = (wet_time / total_time) * 100
    else:
        moisture_percentage = 0  # Default if no time recorded

    # Update the data dictionary
    data["soil_moisture"] = round(moisture_percentage, 2)

    # Print the soil moisture percentage
    print(f"Soil Moisture: {data['soil_moisture']}%")


# HTTP request handler
class SensorRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/sensor-data':
            try:
                # Prepare sensor data
                data = {
                    "ultrasonic_distance": read_ultrasonic(),
                    "soil_moisture": read_soil_moisture()
                }
                # Send response headers
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                # Send the JSON response
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                # Handle any errors
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_message = {"error": str(e)}
                self.wfile.write(json.dumps(error_message).encode())
        else:
            # Handle unknown paths
            self.send_response(404)
            self.end_headers()

# Start the HTTP server
def start_http_server():
    server_address = ('0.0.0.0', 5000)
    httpd = HTTPServer(server_address, SensorRequestHandler)
    print("Starting HTTP server on port 5000...")
    httpd.serve_forever()

# Main Control Logic
try:
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    print("Starting Control Test.")
    black_line_detected = 0  # Counter to detect black lines

    while True:
        left_ir = GPIO.input(LEFT_IR_SENSOR_PIN)
        right_ir = GPIO.input(RIGHT_IR_SENSOR_PIN)

        if left_ir and right_ir:  # Both sensors detect black line
            black_line_detected += 1
            stop_motors()
            data["ir_status"] = "Both IR sensors detect black line."
            print(data["ir_status"])
            time.sleep(2)  # Wait for 2 seconds

            if black_line_detected == 1:  # First black line detection
                run_water_pump_process()  # Call water pump process
                data["checkpoint"] = "First black line detected. Initiating water pump process."
                time.sleep(5)  # Wait for the water pump process to finish

                data["motor_dir"] = "Moving forward after water pump process."
                print(data["motor_dir"])
                set_motor("left_motor", 30)
                set_motor("right_motor", 30)
                time.sleep(0.1)  # Small delay to ensure motors start properly
                
            elif black_line_detected == 2:  # Second black line detection
                run_water_pump_process()  # Call water pump process
                data["checkpoint"] = "Second black line detected. Initiating water pump process again."
                time.sleep(5)  # Wait for the water pump process to finish

                data["motor_dir"] = "Moving forward after second water pump process."
                print(data["motor_dir"])
                set_motor("left_motor", 30)
                set_motor("right_motor", 30)
                time.sleep(0.1)  # Small delay to ensure motors start properly
            
            elif black_line_detected == 3:  # Third black line detection
                run_water_pump_process()  # Call water pump process
                data["checkpoint"] = "Third black line detected. Initiating water pump process again."
                time.sleep(5)  # Wait for the water pump process to finish
                
                data["motor_dir"] = "Exiting after third water pump process."
                print(data["motor_dir"])
                break  # Exit after third water pump process
        
        elif left_ir:  # Left IR detects black line
            data["ir_status"] = "Left IR detects black line. Adjusting right."
            print(data["ir_status"])
            set_motor("left_motor", 50)  # Slight adjustment
            set_motor("right_motor", 30)
            data["motor_dir"] = "Slight adjustment"

        elif right_ir:  # Right IR detects black line
            data["ir_status"] = "Right IR detects black line. Adjusting left."
            print(data["ir_status"])
            set_motor("left_motor", 30)
            set_motor("right_motor", 50)  # Slight adjustment
            data["motor_dir"] = "Slight adjustment"

        else:  # No line detected, go straight
            data["ir_status"] = "No line detected."
            print(data["ir_status"])
            set_motor("left_motor", 50)
            set_motor("right_motor", 50)
            data["motor_dir"] = "Moving straight."

        time.sleep(0.1)  # Small delay for stability

except KeyboardInterrupt:
    print("Test interrupted by user.")
finally:
    stop_motors()
    GPIO.cleanup()
