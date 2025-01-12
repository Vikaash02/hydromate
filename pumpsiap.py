import RPi.GPIO as GPIO
import time

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Define GPIO pins for pulse signal
PUL_PIN = 23  # Pulse Pin
DIR_PIN = 24  # Direction Pin
ENA_PIN = 16  # Enable Pin
RELAY_PIN = 21  # GPIO Pin for Water Pump (relay control)

# Set up GPIO pins
GPIO.setup(PUL_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(ENA_PIN, GPIO.OUT)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Enable the stepper driver
GPIO.output(ENA_PIN, GPIO.LOW)  # LOW to enable, HIGH to disable

# Increase speed by reducing the pulse delay
pulse_delay = 0.001  # Adjust this value for faster or slower rotation (lower = faster)

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

# Main function to be called from Code 1
def run_water_pump_process():
    stop_count = 0  # Counter for 5-second stops
    deactivate_pump()  # Ensure pump is off initially

    # Rotate for 2.5 seconds clockwise
    print("Rotating clockwise for 2.5 seconds...")
    rotate_motor(GPIO.HIGH, 1.2)  # Clockwise rotation for 2.5 seconds

    # Stop for 5 seconds after clockwise rotation
    print("Stopping for 5 seconds...")
    time.sleep(10)  # Stop for 5 seconds
    stop_count += 1

    # Rotate for 2.5 seconds counter-clockwise
    print("Rotating counter-clockwise for 2.5 seconds...")
    rotate_motor(GPIO.LOW, 1.2)  # Counter-clockwise rotation for 2.5 seconds

    stop_count += 1

    # Check if it's the second 5-second stop
    if stop_count == 2:
        print("Second 5-second stop reached. Activating water pump...")
        activate_pump()  # Activate water pump
        time.sleep(5)  # Keep the pump on for 5 seconds
        deactivate_pump()  # Deactivate the pump after 5 seconds
        stop_count = 0  # Reset stop counter after pump activation

