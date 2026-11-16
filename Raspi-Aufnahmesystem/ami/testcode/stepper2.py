from gpiozero import OutputDevice
import time
from time import sleep

STEP_PIN = 20
DIR_PIN = 21

PULSES_PER_REV = 1600
DEFAULT_STEP_DELAY = 0.05
PULSE_WIDTH = 0.0005

step = OutputDevice(STEP_PIN)
direction = OutputDevice(DIR_PIN)
current_position_steps = 0


def move_steps(steps, clockwise=True, step_delay=DEFAULT_STEP_DELAY):
    global current_position_steps

    direction.value = 1 if clockwise else 0
    sleep(0.1)

    for _ in range(steps):
        step.on()
        sleep(PULSE_WIDTH)
        step.off()
        sleep(step_delay)

        if clockwise:
            current_position_steps += 1
        else:
            current_position_steps -= 1


def move_angle(angle_deg, clockwise=True, step_delay=DEFAULT_STEP_DELAY):
    steps = round(PULSES_PER_REV * angle_deg / 360)

    print(f"{angle_deg} degrees = {steps} pulses", flush=True)

    move_steps(
        steps=steps,
        clockwise=clockwise,
        step_delay=step_delay,
    )
    
def get_current_angle():
    return current_position_steps * 360 / PULSES_PER_REV
    
def set_current_angle(angle):
    global current_position_steps

    current_position_steps = round(
        float(angle)
        / 360.0
        * PULSES_PER_REV
    )

def main():

	try:
		time.sleep(3)
		move_angle(15, clockwise=True)
		time.sleep(3)
		move_angle(15, clockwise=False)
		
	
	except KeyboardInterrupt:
		print("\nProgram interrupted.", flush=True)
		
     
if __name__ == "__main__":
    main()
