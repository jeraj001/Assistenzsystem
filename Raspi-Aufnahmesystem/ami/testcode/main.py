import sys
import time
from pathlib import Path

import stepper
import stepper2
import realrecord_func


PAN_TILT_DIR = Path(
    "/home/ami/Pan-Tilt_HAT_code/"
    "RaspberryPi/Servo_Driver/python"
)

sys.path.insert(
    0,
    str(PAN_TILT_DIR),
)

import ttt

CURRENT_PAN_DATASET_ANGLE = 0

PAN_TARGETS = [
    0,
    -45,
    45,
]

STEPPER_TARGETS = [
    60,
    90,
    120,
    150,
    180,
]

START_CONDITION = (
    0,
    60,
    60,
)

ANGLE_TOLERANCE = 2.0

def initialize_pan_reference(
    current_dataset_pan_angle,
):
    current_physical_pan_angle = (
        current_dataset_pan_angle + 90
    )

    if not (
        0
        <= current_physical_pan_angle
        <= 180
    ):
        raise ValueError(
            f"Invalid current dataset "
            f"pan angle: "
            f"{current_dataset_pan_angle}"
        )

    ttt.current_angles[0] = (
        current_physical_pan_angle
    )

    ttt.pwm.setRotationAngle(
        0,
        current_physical_pan_angle,
    )

    print(
        f"Pan software reference "
        f"initialized: "
        f"dataset="
        f"{current_dataset_pan_angle:.2f}, "
        f"control="
        f"{current_physical_pan_angle:.2f}",
        flush=True,
    )

    time.sleep(0.5)
    
def move_motor(
    motor,
    angle,
    clockwise,
):
    print(
        f"Moving motor by "
        f"{angle:.2f} degrees, "
        f"clockwise={clockwise}",
        flush=True,
    )

    motor.move_angle(
        angle,
        clockwise=clockwise,
    )

    time.sleep(1)

def get_dataset_angles():
    raw_stepper1_angle = (
        stepper.get_current_angle()
    )

    raw_stepper2_angle = (
        stepper2.get_current_angle()
    )

    dataset_stepper1_angle = (
        90 - raw_stepper1_angle
    )

    dataset_stepper2_angle = (
        90 + raw_stepper2_angle
    )

    print(
        f"Stepper 1 raw angle: "
        f"{raw_stepper1_angle:.2f}",
        flush=True,
    )

    print(
        f"Stepper 2 raw angle: "
        f"{raw_stepper2_angle:.2f}",
        flush=True,
    )

    print(
        f"Dataset stepper 1 angle: "
        f"{dataset_stepper1_angle:.2f}",
        flush=True,
    )

    print(
        f"Dataset stepper 2 angle: "
        f"{dataset_stepper2_angle:.2f}",
        flush=True,
    )

    return (
        dataset_stepper1_angle,
        dataset_stepper2_angle,
    )


def verify_angle(
    actual_angle,
    expected_angle,
    angle_name,
):
    difference = abs(
        actual_angle - expected_angle
    )

    if difference > ANGLE_TOLERANCE:
        raise RuntimeError(
            f"{angle_name} angle mismatch: "
            f"expected {expected_angle:.2f}, "
            f"got {actual_angle:.2f}"
        )

def initialize_stepper_references():
    stepper.set_current_angle(
        0
    )

    stepper2.set_current_angle(
        0
    )

    (
        dataset_stepper1_angle,
        dataset_stepper2_angle,
    ) = get_dataset_angles()

    verify_angle(
        actual_angle=dataset_stepper1_angle,
        expected_angle=90,
        angle_name=(
            "Stepper 1 initial reference"
        ),
    )

    verify_angle(
        actual_angle=dataset_stepper2_angle,
        expected_angle=90,
        angle_name=(
            "Stepper 2 initial reference"
        ),
    )

    print(
        "Stepper software references "
        "initialized at dataset "
        "position (90, 90).",
        flush=True,
    )


def move_pan_to_dataset_angle(
    dataset_pan_angle,
):
    physical_pan_angle = (
        dataset_pan_angle + 90
    )

    if not 0 <= physical_pan_angle <= 180:
        raise ValueError(
            f"Invalid dataset pan angle: "
            f"{dataset_pan_angle}"
        )

    print(
        f"Moving pan to physical "
        f"{physical_pan_angle:.2f} degrees, "
        f"dataset angle "
        f"{dataset_pan_angle:.2f} degrees.",
        flush=True,
    )

    ttt.move_pan(
        physical_pan_angle
    )

    time.sleep(1)

    return physical_pan_angle

def move_steppers_to(
    target_stepper1_angle,
    target_stepper2_angle,
):
    (
        current_stepper1_angle,
        current_stepper2_angle,
    ) = get_dataset_angles()

    stepper1_difference = (
        target_stepper1_angle
        - current_stepper1_angle
    )

    if abs(stepper1_difference) > (
        ANGLE_TOLERANCE
    ):
        move_motor(
            motor=stepper,
            angle=abs(
                stepper1_difference
            ),
            clockwise=(
                stepper1_difference < 0
            ),
        )

    stepper2_difference = (
        target_stepper2_angle
        - current_stepper2_angle
    )

    if abs(stepper2_difference) > (
        ANGLE_TOLERANCE
    ):
        move_motor(
            motor=stepper2,
            angle=abs(
                stepper2_difference
            ),
            clockwise=(
                stepper2_difference > 0
            ),
        )

    (
        actual_stepper1_angle,
        actual_stepper2_angle,
    ) = get_dataset_angles()

    verify_angle(
        actual_angle=actual_stepper1_angle,
        expected_angle=target_stepper1_angle,
        angle_name="Stepper 1 target",
    )

    verify_angle(
        actual_angle=actual_stepper2_angle,
        expected_angle=target_stepper2_angle,
        angle_name="Stepper 2 target",
    )

def record_current_condition(
    physical_pan_angle,
    expected_stepper1_angle,
    expected_stepper2_angle,
):
    (
        dataset_stepper1_angle,
        dataset_stepper2_angle,
    ) = get_dataset_angles()

    verify_angle(
        actual_angle=dataset_stepper1_angle,
        expected_angle=expected_stepper1_angle,
        angle_name="Stepper 1",
    )

    verify_angle(
        actual_angle=dataset_stepper2_angle,
        expected_angle=expected_stepper2_angle,
        angle_name="Stepper 2",
    )

    dataset_pan_angle = (
        physical_pan_angle - 90
    )

    print("", flush=True)
    print("=" * 70, flush=True)

    print(
        f"Starting recording: "
        f"pan={dataset_pan_angle:.2f}, "
        f"speaker1="
        f"{dataset_stepper1_angle:.2f}, "
        f"speaker2="
        f"{dataset_stepper2_angle:.2f}",
        flush=True,
    )

    print("=" * 70, flush=True)

    realrecord_func.record_clean_database(
        stepper1_angle=(
            dataset_stepper1_angle
        ),
        stepper2_angle=(
            dataset_stepper2_angle
        ),
        pan_angle=dataset_pan_angle,
    )


def build_recording_conditions():
    return [
        (
            pan_angle,
            stepper1_angle,
            stepper2_angle,
        )
        for pan_angle in PAN_TARGETS
        for stepper1_angle in STEPPER_TARGETS
        for stepper2_angle in STEPPER_TARGETS
    ]

def run_from_condition(start_condition):
    conditions = build_recording_conditions()

    if start_condition not in conditions:
        raise ValueError(
            f"Invalid start condition: "
            f"{start_condition}"
        )

    start_index = conditions.index(
        start_condition
    )

    current_pan_dataset_angle = (
        CURRENT_PAN_DATASET_ANGLE
    )

    for (
        target_pan_angle,
        target_stepper1_angle,
        target_stepper2_angle,
    ) in conditions[start_index:]:
        move_steppers_to(
            target_stepper1_angle=(
                target_stepper1_angle
            ),
            target_stepper2_angle=(
                target_stepper2_angle
            ),
        )

        if (
            target_pan_angle
            != current_pan_dataset_angle
        ):
            physical_pan_angle = (
                move_pan_to_dataset_angle(
                    target_pan_angle
                )
            )

            current_pan_dataset_angle = (
                target_pan_angle
            )
        else:
            physical_pan_angle = (
                target_pan_angle + 90
            )

        record_current_condition(
            physical_pan_angle=(
                physical_pan_angle
            ),
            expected_stepper1_angle=(
                target_stepper1_angle
            ),
            expected_stepper2_angle=(
                target_stepper2_angle
            ),
        )

def main():
    ttt.initialize()

    try:
        initialize_stepper_references()
        
        initialize_pan_reference(CURRENT_PAN_DATASET_ANGLE)
        
        time.sleep(3)

        run_from_condition(
            START_CONDITION
        )

        print(
            "All requested recording "
            "conditions completed.",
            flush=True,
        )

    except KeyboardInterrupt:
        print(
            "\nProgram interrupted.",
            flush=True,
        )

    except Exception as error:
        print(
            f"\nProgram failed: {error}",
            flush=True,
        )

        raise

    finally:
        try:
            realrecord_func.write_recording_report()

        except Exception as report_error:
            print(
                f"Failed to write recording "
                f"report: {report_error}",
                flush=True,
            )

        ttt.cleanup(
            return_to_initial=False
        )


if __name__ == "__main__":
    main()
