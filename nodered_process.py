import RPi.GPIO as GPIO
import time
import json
from flask import Flask, jsonify

# Flask server setup
app = Flask(__name__)

# Ultrasonic sensor pins
TRIG = 23
ECHO = 24

# Soil moisture sensor pin
SOIL_MOISTURE_PIN = 17

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(SOIL_MOISTURE_PIN, GPIO.IN)

def read_ultrasonic():
    GPIO.output(TRIG, False)
    time.sleep(2)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance

def read_soil_moisture():
    return GPIO.input(SOIL_MOISTURE_PIN)

@app.route('/sensor-data', methods=['GET'])
def sensor_data():
    data = {
        "water_level": read_ultrasonic(),
        "soil_moisture": read_soil_moisture()
    }
    return jsonify(data)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        GPIO.cleanup()
