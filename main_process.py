import RPi.GPIO as GPIO
import time
import threading
import subprocess

# GPIO Pin Configuration
motor_pins = {
    "left_motor": {"A": 5, "B": 6},  # Pins for left motor
    "right_motor": {"A": 23, "B": 24},  # Pins for right motor
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
current_checkpoint = 0  # Tracks current checkpoint
refill_needed = False
water_refilled = False  # Tracks if water has been refilled

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor Setup
for motor, pins in motor_pins.items():
    GPIO.setup(pins["A"], GPIO.OUT)
    GPIO.setup(pins["B"], GPIO.OUT)

# Motor Control Functions
def set_motor_speed(motor, speed):
    pins = motor_pins[motor]
    if speed > 0:  # Forward
        GPIO.output(pins["A"], GPIO.HIGH)
        GPIO.output(pins["B"], GPIO.LOW)
    elif speed < 0:  # Backward
        GPIO.output(pins["A"], GPIO.LOW)
        GPIO.output(pins["B"], GPIO.HIGH)
    else:  # Stop
        GPIO.output(pins["A"], GPIO.LOW)
        GPIO.output(pins["B"], GPIO.LOW)

def stop_motors():
    for motor in motor_pins:
        GPIO.output(motor_pins[motor]["A"], GPIO.LOW)
        GPIO.output(motor_pins[motor]["B"], GPIO.LOW)

# PID Controller
def pid_control(left_ir, right_ir):
    global previous_error, integral, kp, ki, kd

    error = right_ir - left_ir
    integral += error
    derivative = error - previous_error

    adjustment = (kp * error) + (ki * integral) + (kd * derivative)
    previous_error = error

    # Adjust motor speeds based on PID output
    base_speed = 50  # Base motor speed
    left_speed = base_speed - adjustment
    right_speed = base_speed + adjustment

    # Clamp motor speeds
    left_speed = max(-100, min(100, left_speed))
    right_speed = max(-100, min(100, right_speed))

    set_motor_speed("left_motor", left_speed)
    set_motor_speed("right_motor", right_speed)

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
    global line_counter, current_checkpoint, refill_needed, water_refilled

    while True:
        left_ir = GPIO.input(ir_sensors["left"])
        right_ir = GPIO.input(ir_sensors["right"])

        if left_ir and right_ir:  # Both sensors detect line (checkpoint)
            print(f"Checkpoint {line_counter} detected.")
            stop_motors()
            line_counter += 1
            current_checkpoint = line_counter
            subprocess.run(["python3", "secondary_process.py"])  # Run secondary process
            time.sleep(1)  # Wait for the process to complete
        elif left_ir or right_ir:  # Adjust based on PID
            pid_control(left_ir, right_ir)
        else:  # No line detected, move forward
            set_motor_speed("left_motor", 50)
            set_motor_speed("right_motor", 50)

        # Check water level
        if refill_needed:
            handle_refill()

        time.sleep(0.1)

# Refill Logic
def handle_refill():
    global line_counter, current_checkpoint, refill_needed, water_refilled

    print("Refill needed. Moving to start position.")
    stop_motors()

    # Move backward to start (checkpoint 0)
    while current_checkpoint > 0:
        set_motor_speed("left_motor", -50)  # Negative speed for backward
        set_motor_speed("right_motor", -50)
        time.sleep(1)
        current_checkpoint -= 1  # Simulate reaching the previous checkpoint

    stop_motors()

    print("At refill station. Refilling water tank.")
    while refill_needed:
        check_water_level()
        time.sleep(1)

    water_refilled = True
    print("Tank refilled. Returning to last checkpoint.")

    # Move forward to last checkpoint
    while current_checkpoint < line_counter:
        set_motor_speed("left_motor", 50)
        set_motor_speed("right_motor", 50)
        time.sleep(1)
        current_checkpoint += 1  # Simulate reaching the next checkpoint

    stop_motors()
    print(f"Returned to checkpoint {line_counter}. Resuming process.")
    water_refilled = False

# Main Function
if __name__ == "__main__":
    try:
        # Start the line following and water monitoring in threads
        threading.Thread(target=follow_line, daemon=True).start()
        while True:
            check_water_level()
            if refill_needed and not water_refilled:
                handle_refill()
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        stop_motors()
        GPIO.cleanup()
