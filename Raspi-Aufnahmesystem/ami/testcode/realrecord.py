import math
import os
import re
import signal
import subprocess
import time
from pathlib import Path


SPEECH_ROOT = Path(
    "/home/ami/audiodaten/dev-clean/LibriSpeech/dev-clean"
)

NOISE_ROOT = Path(
    "/home/ami/audiodaten/OMEETING_16k/OMEETING"
)

RECORDING_ROOT = Path(
    "/home/ami/audiodaten/recordings"
)

TEMP_ROOT = Path("/tmp/libri_recording")

AUDIO_DEVICE = "plughw:CARD=Headphones,DEV=0"

RECORD_DEVICE = "hw:CARD=UMA16v2,DEV=0"
RECORD_CHANNELS = 16
RECORD_SAMPLERATE = 48000
RECORD_FORMAT = "S32_LE"

PLAYBACK_SAMPLERATE = 44100
PLAYBACK_BITS = 16

PRE_RECORDING_TIME = 0.5
POST_RECORDING_TIME = 0.5

WINDOWS_USER = "lestileli"
WINDOWS_HOST = "192.168.200.220"
WINDOWS_RECORDING_DIR = (
    "Desktop/praktikum/audio/recordings"
)

TRANSFER_RETRIES = 3
TRANSFER_RETRY_DELAY = 10
DELETE_AFTER_TRANSFER = True

SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".flac",
    ".mp3",
    ".ogg",
    ".m4a",
}


def natural_sort_key(path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def get_speech_folders():
    folders = []

    for path in SPEECH_ROOT.iterdir():
        if not path.is_dir():
            continue

        audio_files = get_audio_files(path)

        if audio_files:
            folders.append(path)

    return sorted(folders, key=natural_sort_key)

def get_audio_files(folder):
    files = [
        path
        for path in folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    ]

    return sorted(
        files,
        key=lambda path: [
            natural_sort_key(part)
            for part in path.relative_to(folder).parents
        ][::-1] + [natural_sort_key(path)]
    )


def get_noise_files():
    files = [
        path
        for path in NOISE_ROOT.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    ]

    return sorted(files, key=natural_sort_key)


def run_command(command):
    print("Running command:", flush=True)
    print(" ".join(str(item) for item in command), flush=True)

    subprocess.run(command, check=True)


def create_speech_track(audio_files, output_file):
    command = [
        "sox",
        *[str(path) for path in audio_files],
        "-r", str(PLAYBACK_SAMPLERATE),
        "-c", "1",
        "-b", str(PLAYBACK_BITS),
        "-e", "signed-integer",
        str(output_file),
    ]

    run_command(command)

def get_audio_duration(audio_file):
    result = subprocess.run(
        [
            "soxi",
            "-D",
            str(audio_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return float(result.stdout.strip())


def create_noise_track(
    noise_files,
    output_file,
    required_duration,
):
    command = [
        "sox",
        *[str(path) for path in noise_files],
        "-r", str(PLAYBACK_SAMPLERATE),
        "-c", "1",
        "-b", str(PLAYBACK_BITS),
        "-e", "signed-integer",
        str(output_file),
        "repeat", "1000",
        "trim", "0", str(required_duration),
    ]

    run_command(command)


def create_stereo_track(
    speech_file,
    noise_file,
    output_file,
):
    command = [
        "sox",
        "-M",
        str(speech_file),
        str(noise_file),
        "-r", str(PLAYBACK_SAMPLERATE),
        "-c", "2",
        "-b", str(PLAYBACK_BITS),
        "-e", "signed-integer",
        str(output_file),
    ]

    run_command(command)

def start_uma16_recording(output_file, duration):
    command = [
        "arecord",
        "-D", RECORD_DEVICE,
        "-c", str(RECORD_CHANNELS),
        "-r", str(RECORD_SAMPLERATE),
        "-f", RECORD_FORMAT,
        "-t", "wav",
        "-d", str(duration),
        str(output_file),
    ]

    print("Recording command:", flush=True)
    print(" ".join(command), flush=True)

    return subprocess.Popen(command)


def stop_recording(record_process):
    if record_process.poll() is not None:
        return

    record_process.send_signal(signal.SIGINT)

    try:
        record_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        record_process.terminate()

        try:
            record_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            record_process.kill()
            record_process.wait()


def play_stereo_file(stereo_file):
    command = [
        "sox",
        str(stereo_file),
        "-t",
        "alsa",
        AUDIO_DEVICE,
    ]

    print("Playback command:", flush=True)
    print(" ".join(command), flush=True)

    subprocess.run(command, check=True)


def prepare_folder_audio(
    speech_folder,
    noise_files,
    folder_number,
):
    speech_files = get_audio_files(speech_folder)

    speech_temp = (
        TEMP_ROOT
        / f"{folder_number:04d}_{speech_folder.name}_speech.wav"
    )

    noise_temp = (
        TEMP_ROOT
        / f"{folder_number:04d}_{speech_folder.name}_noise.wav"
    )

    stereo_temp = (
        TEMP_ROOT
        / f"{folder_number:04d}_{speech_folder.name}_stereo.wav"
    )

    print(
        f"Preparing {len(speech_files)} speech files "
        f"from {speech_folder.name}",
        flush=True,
    )

    create_speech_track(
        audio_files=speech_files,
        output_file=speech_temp,
    )

    speech_duration = get_audio_duration(speech_temp)

    create_noise_track(
        noise_files=noise_files,
        output_file=noise_temp,
        required_duration=speech_duration,
    )

    create_stereo_track(
        speech_file=speech_temp,
        noise_file=noise_temp,
        output_file=stereo_temp,
    )

    return {
        "speech_temp": speech_temp,
        "noise_temp": noise_temp,
        "stereo_temp": stereo_temp,
        "duration": speech_duration,
        "speech_file_count": len(speech_files),
    }

def remove_temporary_files(prepared_audio):
    for key in ["speech_temp", "noise_temp", "stereo_temp"]:
        path = prepared_audio.get(key)

        if path is not None and path.exists():
            path.unlink()

def transfer_recording(output_file):
    remote_target = (
        f"{WINDOWS_USER}@{WINDOWS_HOST}:"
        f"{WINDOWS_RECORDING_DIR}/"
    )

    command = [
        "scp",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        str(output_file),
        remote_target,
    ]

    for attempt in range(1, TRANSFER_RETRIES + 1):
        print(
            f"Transfer attempt "
            f"{attempt}/{TRANSFER_RETRIES}: "
            f"{output_file.name}",
            flush=True,
        )

        result = subprocess.run(
            command,
            check=False,
        )

        if result.returncode == 0:
            print(
                f"Transfer completed: {output_file.name}",
                flush=True,
            )

            if DELETE_AFTER_TRANSFER:
                output_file.unlink()

                print(
                    f"Local recording deleted: {output_file}",
                    flush=True,
                )

            return

        print(
            f"Transfer failed with return code "
            f"{result.returncode}.",
            flush=True,
        )

        if attempt < TRANSFER_RETRIES:
            print(
                f"Retrying in "
                f"{TRANSFER_RETRY_DELAY} seconds.",
                flush=True,
            )

            time.sleep(TRANSFER_RETRY_DELAY)

    raise RuntimeError(
        f"Transfer failed after "
        f"{TRANSFER_RETRIES} attempts. "
        f"Local file was preserved: {output_file}"
    )

def record_folder(
    speech_folder,
    noise_files,
    folder_number,
    total_folders,
):
    print("", flush=True)
    print("=" * 70, flush=True)
    print(
        f"Folder {folder_number}/{total_folders}: "
        f"{speech_folder.name}",
        flush=True,
    )
    print("=" * 70, flush=True)

    prepared_audio = None
    record_process = None

    try:
        prepared_audio = prepare_folder_audio(
            speech_folder=speech_folder,
            noise_files=noise_files,
            folder_number=folder_number,
        )

        playback_duration = prepared_audio["duration"]

        recording_duration = math.ceil(
            PRE_RECORDING_TIME
            + playback_duration
            + POST_RECORDING_TIME
        )

        output_file = (
            RECORDING_ROOT
            / f"{folder_number:04d}_{speech_folder.name}.wav"
        )

        print(
            f"Speech files: "
            f"{prepared_audio['speech_file_count']}",
            flush=True,
        )

        print(
            f"Playback duration: "
            f"{playback_duration:.2f} seconds",
            flush=True,
        )

        print(
            f"Recording duration: "
            f"{recording_duration} seconds",
            flush=True,
        )

        print(
            f"Output file: {output_file}",
            flush=True,
        )

        record_process = start_uma16_recording(
            output_file=output_file,
            duration=recording_duration,
        )

        time.sleep(0.5)

        if record_process.poll() is not None:
            raise RuntimeError(
                "The recording process stopped immediately."
            )

        time.sleep(PRE_RECORDING_TIME)

        play_stereo_file(
            prepared_audio["stereo_temp"]
        )

        time.sleep(POST_RECORDING_TIME)

        stop_recording(record_process)

        if not output_file.exists():
            raise RuntimeError(
                f"Recording file was not created: {output_file}"
            )

        file_size = output_file.stat().st_size

        print(
            f"Saved: {output_file}",
            flush=True,
        )

        print(
            f"File size: {file_size} bytes",
            flush=True,
        )
        
        transfer_recording(output_file)

    except Exception:
        if record_process is not None:
            stop_recording(record_process)

        raise

    finally:
        if prepared_audio is not None:
            remove_temporary_files(prepared_audio)

def main():
    RECORDING_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEMP_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not SPEECH_ROOT.exists():
        raise FileNotFoundError(
            f"Speech directory not found: {SPEECH_ROOT}"
        )

    if not NOISE_ROOT.exists():
        raise FileNotFoundError(
            f"Noise directory not found: {NOISE_ROOT}"
        )

    speech_folders = get_speech_folders()
    noise_files = get_noise_files()

    if not speech_folders:
        raise RuntimeError(
            f"No speech folders found in {SPEECH_ROOT}"
        )

    if not noise_files:
        raise RuntimeError(
            f"No noise files found in {NOISE_ROOT}"
        )

    print(
        f"Speech folders found: {len(speech_folders)}",
        flush=True,
    )

    print(
        f"Noise files found: {len(noise_files)}",
        flush=True,
    )

    print(
        "Speech output: left channel",
        flush=True,
    )

    print(
        "Noise output: right channel",
        flush=True,
    )

    try:
        for folder_number, speech_folder in enumerate(
            speech_folders,
            start=1,
        ):
            record_folder(
                speech_folder=speech_folder,
                noise_files=noise_files,
                folder_number=folder_number,
                total_folders=len(speech_folders),
            )

        print("", flush=True)
        print(
            "All folders have been recorded successfully.",
            flush=True,
        )

    except KeyboardInterrupt:
        print("", flush=True)
        print(
            "Program interrupted by user.",
            flush=True,
        )

    except Exception as error:
        print("", flush=True)
        print(
            f"Error: {error}",
            flush=True,
        )

        raise


if __name__ == "__main__":
    main()
