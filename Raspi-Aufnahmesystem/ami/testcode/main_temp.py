import sys
import time
from pathlib import Path

import realrecord_func
import stepper2


PAN_TILT_DIR = Path(
    "/home/ami/Pan-Tilt_HAT_code/"
    "RaspberryPi/Servo_Driver/python"
)

sys.path.insert(
    0,
    str(PAN_TILT_DIR),
)

import ttt


CURRENT_PAN_DATASET_ANGLE = 45

PAN_TARGETS = [
    0,
    -45,
    45,
]

STEPPER2_TARGETS = [
    60,
    90,
    120,
    150,
    180,
]

START_CONDITION = (
    0,
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


def initialize_stepper2_reference():
    stepper2.set_current_angle(0)

    dataset_stepper2_angle = (
        get_stepper2_dataset_angle()
    )

    verify_angle(
        actual_angle=dataset_stepper2_angle,
        expected_angle=90,
        angle_name=(
            "Stepper 2 initial reference"
        ),
    )

    print(
        "Stepper 2 software reference "
        "initialized at dataset "
        "position 90.",
        flush=True,
    )

def get_stepper2_dataset_angle():
    raw_stepper2_angle = (
        stepper2.get_current_angle()
    )

    dataset_stepper2_angle = (
        90 + raw_stepper2_angle
    )

    print(
        f"Stepper 2 raw angle: "
        f"{raw_stepper2_angle:.2f}",
        flush=True,
    )

    print(
        f"Dataset stepper 2 angle: "
        f"{dataset_stepper2_angle:.2f}",
        flush=True,
    )

    return dataset_stepper2_angle


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


def move_stepper2_to(
    target_stepper2_angle,
):
    current_stepper2_angle = (
        get_stepper2_dataset_angle()
    )

    difference = (
        target_stepper2_angle
        - current_stepper2_angle
    )

    if abs(difference) > ANGLE_TOLERANCE:
        print(
            f"Moving stepper 2 by "
            f"{abs(difference):.2f} degrees, "
            f"clockwise={difference > 0}",
            flush=True,
        )

        stepper2.move_angle(
            abs(difference),
            clockwise=(difference > 0),
        )

        time.sleep(1)

    actual_stepper2_angle = (
        get_stepper2_dataset_angle()
    )

    verify_angle(
        actual_angle=actual_stepper2_angle,
        expected_angle=target_stepper2_angle,
        angle_name="Stepper 2 target",
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


def record_current_condition(
    physical_pan_angle,
    expected_stepper2_angle,
):
    dataset_stepper2_angle = (
        get_stepper2_dataset_angle()
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
        f"speaker1=off, "
        f"speaker2="
        f"{dataset_stepper2_angle:.2f}",
        flush=True,
    )

    print("=" * 70, flush=True)

    realrecord_func.record_clean_database(
        stepper1_angle=None,
        stepper2_angle=(
            dataset_stepper2_angle
        ),
        pan_angle=dataset_pan_angle,
    )

def build_recording_conditions():
    return [
        (
            pan_angle,
            stepper2_angle,
        )
        for pan_angle in PAN_TARGETS
        for stepper2_angle in (
            STEPPER2_TARGETS
        )
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
        target_stepper2_angle,
    ) in conditions[start_index:]:
        move_stepper2_to(
            target_stepper2_angle
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
            expected_stepper2_angle=(
                target_stepper2_angle
            ),
        )


def main():
    ttt.initialize()

    try:
        initialize_stepper2_reference()

        initialize_pan_reference(
            CURRENT_PAN_DATASET_ANGLE
        )

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
