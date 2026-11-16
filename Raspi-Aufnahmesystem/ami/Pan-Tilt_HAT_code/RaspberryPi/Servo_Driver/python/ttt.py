from PCA9685 import PCA9685
import time

INITIAL_ANGLES = {
    0: 45,
    1: 40,
}

DEFAULT_STEP = 1
DEFAULT_DELAY = 0.05

current_angles = INITIAL_ANGLES.copy()
pwm = None


def initialize():
    global pwm

    if pwm is None:
        pwm = PCA9685()
        pwm.setPWMFreq(50)


def move_slow(channel, target_angle, step=DEFAULT_STEP, delay=DEFAULT_DELAY):
    if pwm is None:
        raise RuntimeError("Call initialize() before moving the servos.")

    if channel not in current_angles:
        raise ValueError(f"Invalid channel: {channel}")

    if not 0 <= target_angle <= 180:
        raise ValueError("Angle must be between 0 and 180.")

    if step <= 0:
        raise ValueError("Step must be greater than 0.")

    if delay < 0:
        raise ValueError("Delay must not be negative.")

    angle = current_angles[channel]

    while angle != target_angle:
        if angle < target_angle:
            angle = min(angle + step, target_angle)
        else:
            angle = max(angle - step, target_angle)

        pwm.setRotationAngle(channel, angle)
        current_angles[channel] = angle
        time.sleep(delay)


def move_pan(target_angle, step=DEFAULT_STEP, delay=DEFAULT_DELAY):
    move_slow(
        channel=0,
        target_angle=target_angle,
        step=step,
        delay=delay,
    )


def move_tilt(target_angle, step=DEFAULT_STEP, delay=DEFAULT_DELAY):
    move_slow(
        channel=1,
        target_angle=target_angle,
        step=step,
        delay=delay,
    )


def return_to_initial_positions():
    move_pan(INITIAL_ANGLES[0])
    move_tilt(INITIAL_ANGLES[1])


def cleanup(return_to_initial=True):
    global pwm

    if pwm is None:
        return

    if return_to_initial:
        return_to_initial_positions()
        time.sleep(0.5)

    pwm.exit_PCA9685()
    pwm = None

def main():
	initialize()
	try:
		time.sleep(1)
		move_pan(90)
		time.sleep(2)
		move_pan(45
		)
		
	
	except KeyboardInterrupt:
		print("\nProgram interrupted.", flush=True)
		
	finally:
		cleanup(return_to_initial=False)
     
if __name__ == "__main__":
    main()

