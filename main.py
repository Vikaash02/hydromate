import RPi.GPIO as GPIO
import time
import importlib

# GPIO Pin Configuration for Motors and IR Sensors
motor_pins = {
    "left_motor": {"A": 6, "B": 26},  # Pins for left motor
    "right_motor": {"A": 22, "B": 5},  # Pins for right motor
}
# GPIO Pin Configuration for IR Sensors
ir_sensors = {
    "left": 17,  # Left IR sensor pin
    "right": 27,  # Right IR sensor pin
}

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup Motor Pins
for motor, pins in motor_pins.items():
    GPIO.setup(pins["A"], GPIO.OUT)
    GPIO.setup(pins["B"], GPIO.OUT)

# Setup IR Sensor Pins
for sensor in ir_sensors.values():
    GPIO.setup(sensor, GPIO.IN)

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

# Main IR Control Logic
try:
    print("Starting IR Control Test.")
    black_line_detected = 0  # Counter to detect black lines
    water_pump_control = importlib.import_module('pumpsiap')

    while True:
        left_ir = GPIO.input(ir_sensors["left"])
        right_ir = GPIO.input(ir_sensors["right"])

        if left_ir and right_ir:  # Both sensors detect black line
            print("Both IR sensors detect black line.")
            black_line_detected += 1
            stop_motors()
            time.sleep(2)  # Wait for 2 seconds

            if black_line_detected == 1:  # First black line detection
                print("First black line detected. Initiating water pump process.")
                water_pump_control.run_water_pump_process()  # Call water pump process
                time.sleep(5)  # Wait for the water pump process to finish
                print("Resuming line following after water pump process.")
                print("Resuming line following after water pump process.")

                # Re-start line following movement after water pump process
                print("Moving forward after water pump process.")
                set_motor("left_motor", 30)
                set_motor("right_motor", 30)
                time.sleep(0.1)  # Small delay to ensure motors start properly
                
            elif black_line_detected == 2:  # Second black line detection
                print("Second black line detected. Initiating water pump process again.")
                water_pump_control.run_water_pump_process()  # Call water pump process
                time.sleep(5)  # Wait for the water pump process to finish
                print("Resuming line following after water pump process.")
                
                # Re-start line following movement after second water pump process
                print("Moving forward after second water pump process.")
                set_motor("left_motor", 30)
                set_motor("right_motor", 30)
                time.sleep(0.1)  # Small delay to ensure motors start properly
            
            elif black_line_detected == 3:  # Third black line detection
                print("Third black line detected. Initiating water pump process again.")
                water_pump_control.run_water_pump_process()  # Call water pump process
                time.sleep(5)  # Wait for the water pump process to finish
                print("Exiting after third water pump process.")
                break  # Exit after third water pump process

        
        elif left_ir:  # Left IR detects black line
            print("Left IR detects black line. Adjusting right.")
            set_motor("left_motor", 50)  # Slight adjustment
            set_motor("right_motor", 30)
        elif right_ir:  # Right IR detects black line
            print("Right IR detects black line. Adjusting left.")
            set_motor("left_motor", 30)
            set_motor("right_motor", 50)  # Slight adjustment
        else:  # No line detected, go straight
            print("No line detected. Moving straight.")
            set_motor("left_motor", 50)
            set_motor("right_motor", 50)

        time.sleep(0.1)  # Small delay for stability

except KeyboardInterrupt:
    print("Test interrupted by user.")
finally:
    stop_motors()
    GPIO.cleanup()

