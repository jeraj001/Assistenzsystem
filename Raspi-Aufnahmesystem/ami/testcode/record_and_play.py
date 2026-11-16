import os
import shutil
import signal
import subprocess
import sys
import time

MIC_DEVICE = "plughw:3,0"
RECORD_RATE = "16000"
RECORD_CHANNELS = "1"
RECORD_FORMAT = "S16_LE"
RECORD_FILE = "/home/ami/record1.wav"

SINK_ANALOG = "alsa_output.platform-fe00b840.mailbox.stereo-fallback"
SINK_BLUETOOTH = "bluez_output.B4_E7_B3_52_0C_8B.1"

FILE_ANALOG = "/home/ami/record.wav"
FILE_BLUETOOTH = "/home/ami/test.wav"

RECORD_SECONDS = 5


def check_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command not found: {name}")


def check_file(path: str) -> None:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Audio file not found: {path}")


def start_recording() -> subprocess.Popen:
    cmd = [
        "arecord",
        "-D", MIC_DEVICE,
        "-f", RECORD_FORMAT,
        "-r", RECORD_RATE,
        "-c", RECORD_CHANNELS,
        "-d", str(RECORD_SECONDS),
        RECORD_FILE,
    ]
    print("Starting recording...")
    return subprocess.Popen(cmd)


def start_playback(sink: str, file_path: str) -> subprocess.Popen:
    env = os.environ.copy()
    env["PULSE_SINK"] = sink
    cmd = ["paplay", file_path]
    print(f"Starting playback on sink: {sink}")
    print(f"File: {file_path}")
    return subprocess.Popen(cmd, env=env)


def terminate_process(proc: subprocess.Popen | None, name: str) -> None:
    if proc is None:
        return
    if proc.poll() is not None:
        return

    print(f"Stopping {name}...")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def main() -> int:
    try:
        check_command("arecord")
        check_command("paplay")
        check_file(FILE_ANALOG)
        check_file(FILE_BLUETOOTH)

        record_proc = start_recording()
        time.sleep(0.2)

        analog_proc = start_playback(SINK_ANALOG, FILE_ANALOG)
        time.sleep(0.2)

        bt_proc = start_playback(SINK_BLUETOOTH, FILE_BLUETOOTH)

        try:
            record_code = record_proc.wait()
            analog_code = analog_proc.wait()
            bt_code = bt_proc.wait()
        except KeyboardInterrupt:
            print("Interrupted by user.")
            terminate_process(record_proc, "recording")
            terminate_process(analog_proc, "analog playback")
            terminate_process(bt_proc, "bluetooth playback")
            return 1

        print(f"Recording exit code: {record_code}")
        print(f"Analog playback exit code: {analog_code}")
        print(f"Bluetooth playback exit code: {bt_code}")

        if record_code != 0 or analog_code != 0 or bt_code != 0:
            return 1

        print("All tasks finished successfully.")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
