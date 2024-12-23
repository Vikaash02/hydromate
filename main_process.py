import RPi.GPIO as GPIO
import time
import threading
import subprocess

# GPIO Pin Configuration
motor_pins = {
    "left_motor": {"pwm": 12, "dir1": 5, "dir2": 6},
    "right_motor": {"pwm": 13, "dir1": 23, "dir2": 24},
}
ir_sensors = {"left": 17, "right": 27}
ultrasonic_pins = {"trigger": 20, "echo": 21}

# PID Controller Variables
kp = 1.0  # Proportional gain
ki = 0.1  # Integral gain
kd = 0.05  # Derivative gain
previous_error = 0
integral = 0

# State Variables
line_counter = 0
current_position = 0  # Tracks position on the line
refill_needed = False

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor Setup
for motor, pins in motor_pins.items():
    GPIO.setup(pins["pwm"], GPIO.OUT)
    GPIO.setup(pins["dir1"], GPIO.OUT)
    GPIO.setup(pins["dir2"], GPIO.OUT)

pwm_controls = {}
for motor, pins in motor_pins.items():
    pwm_controls[motor] = GPIO.PWM(pins["pwm"], 100)  # 100 Hz PWM frequency
    pwm_controls[motor].start(0)

# IR Sensors and Ultrasonic Sensor Setup
for sensor in ir_sensors.values():
    GPIO.setup(sensor, GPIO.IN)
GPIO.setup(ultrasonic_pins["trigger"], GPIO.OUT)
GPIO.setup(ultrasonic_pins["echo"], GPIO.IN)

# Motor Control Functions
def set_motor_speed(motor, speed, direction):
    pins = motor_pins[motor]
    GPIO.output(pins["dir1"], GPIO.HIGH if direction == "forward" else GPIO.LOW)
    GPIO.output(pins["dir2"], GPIO.LOW if direction == "forward" else GPIO.HIGH)
    pwm_controls[motor].ChangeDutyCycle(abs(speed))

def stop_motors():
    for motor in motor_pins:
        pwm_controls[motor].ChangeDutyCycle(0)

# PID Controller
def pid_control(left_ir, right_ir):
    global previous_error, integral

    error = right_ir - left_ir
    integral += error
    derivative = error - previous_error

    adjustment = (kp * error) + (ki * integral) + (kd * derivative)
    previous_error = error

    # Adjust motor speeds based on PID output
    base_speed = 50  # Base motor speed
    set_motor_speed("left_motor", base_speed - adjustment, "forward")
    set_motor_speed("right_motor", base_speed + adjustment, "forward")

# Ultrasonic Sensor Functions
def get_distance():
    GPIO.output(ultrasonic_pins["trigger"], True)
    time.sleep(0.00001)
    GPIO.output(ultrasonic_pins["trigger"], False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ultrasonic_pins["echo"]) == 0:
        start_time = time.time()
    while GPIO.input(ultrasonic_pins["echo"]) == 1:
        stop_time = time.time()

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2  # Distance in cm
    return distance

def check_water_level():
    global refill_needed
    distance = get_distance()
    if distance > 30:  # Adjust threshold as needed
        refill_needed = True
    else:
        refill_needed = False

# Line Following Logic
def follow_line():
    global line_counter, current_position

    while True:
        left_ir = GPIO.input(ir_sensors["left"])
        right_ir = GPIO.input(ir_sensors["right"])

        if left_ir and right_ir:  # Both sensors detect line (stop sign)
            print("Stop sign detected.")
            stop_motors()
            line_counter += 1
            subprocess.run(["python3", "secondary_process.py"])  # Run another script
            time.sleep(1)  # Wait for the process to complete
        elif left_ir or right_ir:  # Adjust based on PID
            pid_control(left_ir, right_ir)
        else:  # No line detected, move forward
            set_motor_speed("left_motor", 50, "forward")
            set_motor_speed("right_motor", 50, "forward")

        time.sleep(0.1)

# Refill Logic
def handle_refill():
    global line_counter, current_position

    if refill_needed:
        print("Refill needed. Moving to refill station.")
        stop_motors()
        while get_distance() > 10:  # Move backward until near refill station
            set_motor_speed("left_motor", 50, "backward")
            set_motor_speed("right_motor", 50, "backward")
        stop_motors()

        print("At refill station. Waiting for tank to refill.")
        while refill_needed:
            check_water_level()
            time.sleep(1)

        print("Tank refilled. Returning to last stop.")
        for _ in range(line_counter):  # Return to the original line count
            set_motor_speed("left_motor", 50, "forward")
            set_motor_speed("right_motor", 50, "forward")
            time.sleep(1)  # Simulate returning

        print("Back to position. Resuming process.")

# Main Function
if __name__ == "__main__":
    try:
        # Start the line following and water monitoring in threads
        threading.Thread(target=follow_line, daemon=True).start()
        while True:
            check_water_level()
            if refill_needed:
                handle_refill()
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        stop_motors()
        GPIO.cleanup()
