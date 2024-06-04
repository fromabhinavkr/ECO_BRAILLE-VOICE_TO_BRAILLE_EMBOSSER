from time import sleep, time
import RPi.GPIO as GPIO

# Set up the GPIO pins
DIR = 22  # Direction GPIO Pin
STEP = 23  # Step GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation
SPR = 24   # Steps per Revolution (360 / 7.5)

# Set up the GPIO mode and pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Set the number of steps and the delay
step_count = SPR # Decrease the number of steps
delay = 0.005 # Increase the delay

try:
    # Spin the motor in one direction for 10 seconds
    GPIO.output(DIR, CW)
    start_time = time()
    while time() - start_time < 10:
        for x in range(step_count):
            GPIO.output(STEP, GPIO.HIGH)
            sleep(delay)
            GPIO.output(STEP, GPIO.LOW)
            sleep(delay)

    # Spin the motor in the opposite direction for 10 seconds
    GPIO.output(DIR, CCW)
    start_time = time()
    while time() - start_time < 10:
        for x in range(step_count):
            GPIO.output(STEP, GPIO.HIGH)
            sleep(delay)
            GPIO.output(STEP, GPIO.LOW)
            sleep(delay)

except KeyboardInterrupt:
    # Clean up the GPIO pins when the user presses Ctrl+C
    GPIO.cleanup()

except Exception as e:
    # Print an error message if there is an exception
    print("An error occurred: ", str(e))
    # Clean up the GPIO pins
    GPIO.cleanup()

# Clean up the GPIO pins at the end of the script
GPIO.cleanup()
