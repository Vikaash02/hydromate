import RPi.GPIO as GPIO
import time
from flask import Flask, jsonify

# Flask setup
app = Flask(__name__)

# GPIO setup
GPIO.setmode(GPIO.BCM)

# IR sensor pins
LEFT_IR_SENSOR_PIN = 17
RIGHT_IR_SENSOR_PIN = 27
GPIO.setup(LEFT_IR_SENSOR_PIN, GPIO.IN)
GPIO.setup(RIGHT_IR_SENSOR_PIN, GPIO.IN)

# Ultrasonic sensor setup
TRIG = 23
ECHO = 24
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

# Flask route to provide sensor data
@app.route('/sensor-data', methods=['GET'])
def sensor_data():
    try:
        data = {
            "ir_status": check_ir_sensors(),
            "ultrasonic_distance": read_ultrasonic()
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        GPIO.cleanup()
