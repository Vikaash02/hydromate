import RPi.GPIO as GPIO
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# GPIO setup
GPIO.setmode(GPIO.BCM)

# IR sensor pins
LEFT_IR_SENSOR_PIN = 17
RIGHT_IR_SENSOR_PIN = 27
GPIO.setup(LEFT_IR_SENSOR_PIN, GPIO.IN)
GPIO.setup(RIGHT_IR_SENSOR_PIN, GPIO.IN)


SOIL_PIN = 7  # GPIO pin connected to the digital output
GPIO.setup(SOIL_PIN, GPIO.IN)

# Ultrasonic sensor setup
TRIG = 13
ECHO = 1
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Read ultrasonic sensor
def read_ultrasonic():
    GPIO.output(TRIG, False)
    time.sleep(0.1)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

# Read IR sensors
def check_ir_sensors():
    left = GPIO.input(LEFT_IR_SENSOR_PIN)
    right = GPIO.input(RIGHT_IR_SENSOR_PIN)
    if left == 0 and right == 0:
        return "Both sensors detect a black line"
    elif left == 0:
        return "Left sensor detects a black line"
    elif right == 0:
        return "Right sensor detects a black line"
    else:
        return "No black line detected"
    
def read_soil_moisture():
    wet_time = 0
    dry_time = 0
    start_time = time.time()
    
    # Read the current state
    state = GPIO.input(SOIL_PIN)
        
    # Update time counters
    current_time = time.time()
    if state == 0:  # Wet state
        wet_time += current_time - start_time
    else:  # Dry state
        dry_time += current_time - start_time
        
    # Reset start_time for the next loop
    start_time = current_time
        
    # Calculate percentage of wetness
    total_time = wet_time + dry_time
    if total_time > 0:
        moisture_percentage = (wet_time / total_time) * 100
    else:
        moisture_percentage = 0  # Default at startup
        
    # Print the moisture percentage
    print(f"Soil Moisture: {moisture_percentage:.2f}%")
    time.sleep(1)
    

# HTTP request handler
class SensorRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/sensor-data':
            try:
                # Prepare sensor data
                data = {
                    "ir_status": check_ir_sensors(),
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
def run_server():
    server_address = ('0.0.0.0', 5000)
    httpd = HTTPServer(server_address, SensorRequestHandler)
    print("Starting HTTP server on port 5000...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()
        GPIO.cleanup()

if __name__ == '__main__':
    run_server()

