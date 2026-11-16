from PCA9685 import PCA9685
import time

pwm = PCA9685()
pwm.setPWMFreq(50)

try:
    print("Move to safe middle position...")
    pwm.setRotationAngle(1, 90)
    pwm.setRotationAngle(0, 90)
    time.sleep(2)
    print("Small movement test: tilt")
    pwm.setRotationAngle(1, 80)
    time.sleep(1)
    pwm.setRotationAngle(1, 100)
    time.sleep(1)
    pwm.setRotationAngle(1, 90)
    time.sleep(1)

    print("Small movement test: pan")
    pwm.setRotationAngle(0, 80)
    time.sleep(1)
    pwm.setRotationAngle(0, 100)
    time.sleep(1)
    pwm.setRotationAngle(0, 90)
    time.sleep(1)

    print("Test finished.")

finally:
    pwm.exit_PCA9685()
