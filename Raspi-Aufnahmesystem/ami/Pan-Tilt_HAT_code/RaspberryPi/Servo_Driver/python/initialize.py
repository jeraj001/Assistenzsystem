from PCA9685 import PCA9685
import time

INITIAL_ANGLES = {
    0: 90,
    1: 50,
}

pwm = PCA9685()
pwm.setPWMFreq(50)

try:
    print("Moving servos to initial positions...", flush=True)

    pwm.setRotationAngle(0, INITIAL_ANGLES[0])
    pwm.setRotationAngle(1, INITIAL_ANGLES[1])

    time.sleep(2)

    print("Initial positions reached.", flush=True)
    print("Channel 0: 45 degrees", flush=True)
    print("Channel 1: 70 degrees", flush=True)
    print("Press Enter to finish.", flush=True)

    input()

finally:
    pwm.exit_PCA9685()
