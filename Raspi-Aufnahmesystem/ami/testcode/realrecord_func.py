import math
import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path
import json
from datetime import datetime

SPEECH_ROOT = Path(
    "/home/ami/audiodaten/normalized_-32LUFS/LibriSpeech"
)

TRANSCRIPT_FILE = (
    SPEECH_ROOT / "transcript.txt"
)

NOISE_ROOT = Path(
    "/home/ami/audiodaten/normalized_-32LUFS/OMEETING"
)

RECORDING_ROOT = Path(
    "/home/ami/audiodaten/recordings"
)

TEMP_ROOT = Path(
    "/dev/shm/clean_recording"
)

BATCH_COUNTER_FILE = (
    RECORDING_ROOT / ".next_batch_number"
)

AUDIO_DEVICE = "plughw:CARD=Headphones,DEV=0"

RECORD_DEVICE = "hw:CARD=UMA16v2,DEV=0"
RECORD_CHANNELS = 16
RECORD_SAMPLERATE = 48000
RECORD_FORMAT = "S32_LE"

PLAYBACK_SAMPLERATE = 44100
PLAYBACK_BITS = 16
LEFT_VOLUME = 0.4
RIGHT_VOLUME = 1.0

PRE_RECORDING_TIME = 0.5
POST_RECORDING_TIME = 0.2
RECORDING_RETRIES = 5
RECORDING_RETRY_DELAY = 2

WARMUP_RETRIES = 3
WARMUP_DURATION = 2

PLAYBACK_BUFFER_TIME = 1000000
PLAYBACK_PERIOD_TIME = 200000

RECORD_BUFFER_TIME = 1000000
RECORD_PERIOD_TIME = 200000

RECORDING_DURATION_TOLERANCE = 0.25

RECORDING_ISSUES = []

WINDOWS_USER = "lestileli"
WINDOWS_HOST = "192.168.200.220"
WINDOWS_RECORDING_DIR = (
    "Desktop/praktikum/audio/recordings"
)

TRANSFER_RETRIES = 3
TRANSFER_RETRY_DELAY = 10
DELETE_AFTER_TRANSFER = True


TRANSFER_MODE = "usb"

USB_MOUNT_POINT = Path(
    "/media/ami/TPU301"
)

USB_RECORDING_ROOT = (
    USB_MOUNT_POINT / "recordings"
)

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

def format_angle(angle):
    rounded_angle = int(
        round(float(angle))
    )

    if rounded_angle >= 0:
        prefix = "p"
    else:
        prefix = "m"

    return (
        f"{prefix}"
        f"{abs(rounded_angle):03d}"
    )


def format_stepper_angle(angle):
    nominal_angle = round(
        float(angle) / 30
    ) * 30

    return format_angle(
        nominal_angle
    )
    
def get_audio_files(folder):
    files = [
        path
        for path in folder.iterdir()
        if path.is_file()
        and path.suffix.lower()
        in SUPPORTED_AUDIO_EXTENSIONS
    ]

    return sorted(files, key=natural_sort_key)

def load_transcripts():
    if not TRANSCRIPT_FILE.exists():
        raise FileNotFoundError(
            f"Transcript file not found: "
            f"{TRANSCRIPT_FILE}"
        )

    transcripts = {}

    with TRANSCRIPT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            parts = line.split(
                maxsplit=1
            )

            if len(parts) != 2:
                raise ValueError(
                    f"Invalid transcript at line "
                    f"{line_number}: {line}"
                )

            recording_id = parts[0]
            transcript = parts[1]

            if recording_id in transcripts:
                raise ValueError(
                    f"Duplicate transcript ID: "
                    f"{recording_id}"
                )

            transcripts[recording_id] = (
                transcript
            )

    return transcripts

def parse_speech_identifiers(speech_file):
    parts = speech_file.stem.split("-", maxsplit=1)

    if len(parts) != 2:
        raise ValueError(
            f"Invalid speech filename: {speech_file.name}"
        )

    speaker_id = parts[0]
    content_id = parts[1]

    return speaker_id, content_id


def get_noise_dataset_name():
    return NOISE_ROOT.parent.name.replace("_", "-")


def write_metadata(
    metadata_file,
    speech_file,
    transcript,
    noise_name,
    stepper1_angle,
    stepper2_angle,
    pan_angle,
):
    speaker_id, content_id = (
        parse_speech_identifiers(
            speech_file
        )
    )

    metadata = {
        "speaker_id": speaker_id,
        "content_id": content_id,
        "transcript": transcript,
        "noise_name": noise_name,
        "stepper_1_angle": (
            None
            if stepper1_angle is None
            else float(stepper1_angle)
        ),
        "stepper_2_angle": (
            None
            if stepper2_angle is None
            else float(stepper2_angle)
        ),
        "pan_angle": float(
            pan_angle
        ),
        "speech_volume_factor": (
            LEFT_VOLUME
        ),
        "noise_volume_factor": (
            RIGHT_VOLUME
        ),
    }

    temporary_file = (
        metadata_file.with_name(
            metadata_file.name
            + ".partial"
        )
    )

    temporary_file.write_text(
        json.dumps(
            metadata,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temporary_file.replace(
        metadata_file
    )

    print(
        f"Metadata saved: "
        f"{metadata_file}",
        flush=True,
    )


def terminate_process(process, first_signal):
    if process is None:
        return

    if process.poll() is not None:
        return

    try:
        os.killpg(process.pid, first_signal)
    except ProcessLookupError:
        return

    try:
        process.wait(timeout=10)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return

    process.wait()


def run_checked(command):
    print("Running command:", flush=True)
    print(
        " ".join(str(item) for item in command),
        flush=True,
    )

    process = subprocess.Popen(
        command,
        start_new_session=True,
    )

    try:
        return_code = process.wait()
    except BaseException:
        terminate_process(
            process,
            signal.SIGINT,
        )
        raise

    if return_code != 0:
        raise subprocess.CalledProcessError(
            return_code,
            command,
        )

def create_mono_track(
    input_file,
    output_file,
):
    command = [
        "sox",
        str(input_file),
        "-r", str(PLAYBACK_SAMPLERATE),
        "-c", "1",
        "-b", str(PLAYBACK_BITS),
        "-e", "signed-integer",
        str(output_file),
    ]

    run_checked(command)


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
    noise_file,
    output_file,
    required_duration,
):
    command = [
        "sox",
        str(noise_file),
        "-r", str(PLAYBACK_SAMPLERATE),
        "-c", "1",
        "-b", str(PLAYBACK_BITS),
        "-e", "signed-integer",
        str(output_file),
        "repeat", "1000",
        "trim", "0", str(required_duration),
    ]

    run_checked(command)


def create_stereo_track(
    speech_file,
    noise_file,
    output_file,
):
    command = [
        "sox",
        "-M",
        "-v", str(LEFT_VOLUME),
        str(noise_file),
        "-v", str(RIGHT_VOLUME),
        str(speech_file),
        "-r", str(PLAYBACK_SAMPLERATE),
        "-c", "2",
        "-b", str(PLAYBACK_BITS),
        "-e", "signed-integer",
        str(output_file),
    ]

    run_checked(command)


def prepare_audio(
    speech_source,
    noise_source,
    item_number,
):
    speech_temp = (
        TEMP_ROOT
        / f"{item_number:04d}_speech.wav"
    )

    noise_temp = (
        TEMP_ROOT
        / f"{item_number:04d}_noise.wav"
    )

    stereo_temp = (
        TEMP_ROOT
        / f"{item_number:04d}_stereo.wav"
    )

    create_mono_track(
        input_file=speech_source,
        output_file=speech_temp,
    )

    speech_duration = get_audio_duration(
        speech_temp
    )

    create_noise_track(
        noise_file=noise_source,
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
    }


def remove_temporary_files(item_number):
    names = [
        f"{item_number:04d}_speech.wav",
        f"{item_number:04d}_noise.wav",
        f"{item_number:04d}_stereo.wav",
    ]

    for name in names:
        path = TEMP_ROOT / name

        if path.exists():
            path.unlink()

def warm_up_recording_device():
    command = [
        "arecord",
        "-D", RECORD_DEVICE,
        "-c", str(RECORD_CHANNELS),
        "-r", str(RECORD_SAMPLERATE),
        "-f", RECORD_FORMAT,
        "-t", "raw",
        "-d", str(WARMUP_DURATION),
        "/dev/null",
    ]

    for attempt in range(
        1,
        WARMUP_RETRIES + 1,
    ):
        print(
            f"Recording device warm-up "
            f"{attempt}/{WARMUP_RETRIES}",
            flush=True,
        )

        try:
            run_checked(command)

            print(
                "Recording device warm-up completed.",
                flush=True,
            )

            return

        except subprocess.CalledProcessError as error:
            print(
                f"Warm-up failed with return code "
                f"{error.returncode}.",
                flush=True,
            )

            if attempt < WARMUP_RETRIES:
                time.sleep(2)

    raise RuntimeError(
        "The recording device could not be initialized."
    )

def start_recording(output_file):
    command = [
        "arecord",
        "--fatal-errors",
        "-D", RECORD_DEVICE,
        "-c", str(RECORD_CHANNELS),
        "-r", str(RECORD_SAMPLERATE),
        "-f", RECORD_FORMAT,
        "-t", "wav",
        f"--buffer-time={RECORD_BUFFER_TIME}",
        f"--period-time={RECORD_PERIOD_TIME}",
        str(output_file),
    ]

    print("Recording command:", flush=True)
    print(" ".join(command), flush=True)

    return subprocess.Popen(
        command,
        start_new_session=True,
    )


def stop_recording(record_process):
    terminate_process(
        record_process,
        signal.SIGINT,
    )


def play_stereo_file(stereo_file):
    command = [
        "aplay",
        "-D", AUDIO_DEVICE,
        f"--buffer-time={PLAYBACK_BUFFER_TIME}",
        f"--period-time={PLAYBACK_PERIOD_TIME}",
        str(stereo_file),
    ]

    run_checked(command)


def create_condition_folder(
    noise_name,
    pan_angle,
    stepper1_angle,
    stepper2_angle,
):
    noise_folder = (
        RECORDING_ROOT
        / f"noise_{noise_name}"
    )

    microphone_folder = (
        noise_folder
        / f"mic_{format_angle(pan_angle)}"
    )
    
    if stepper1_angle is None:
        speaker_folder_name = (
            "speaker_"
            f"s2_{format_stepper_angle(stepper2_angle)}_"
            "s1_off"
        )
    elif stepper2_angle is None:
        speaker_folder_name = (
            "speaker_"
            f"s1_{format_stepper_angle(stepper1_angle)}_"
            "s2_off"
        )
    else:
        speaker_folder_name = (
            "speaker_"
            f"s1_{format_stepper_angle(stepper1_angle)}_"
            f"s2_{format_stepper_angle(stepper2_angle)}"
        )

    speaker_folder = (
        microphone_folder
        / speaker_folder_name
    )

    speaker_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return speaker_folder

def validate_recording(
    recording_file,
    expected_duration,
):
    if not recording_file.exists():
        raise RuntimeError(
            f"Recording file was not created: "
            f"{recording_file}"
        )

    minimum_size = int(
        expected_duration
        * RECORD_SAMPLERATE
        * RECORD_CHANNELS
        * 4
    )

    actual_size = (
        recording_file.stat().st_size
    )

    if actual_size < minimum_size:
        recording_file.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            f"Incomplete recording: "
            f"expected at least "
            f"{minimum_size} bytes, "
            f"got {actual_size} bytes"
        )

def record_one_file(
    speech_file,
    transcript,
    noise_file,
    noise_name,
    output_folder,
    item_number,
    total_items,
    stepper1_angle,
    stepper2_angle,
    pan_angle,
):
    print("", flush=True)
    print("=" * 70, flush=True)
    print(
        f"Recording {item_number}/{total_items}",
        flush=True,
    )
    print(
        f"Speech: {speech_file.name}",
        flush=True,
    )
    print(
        f"Noise file: {noise_file.name}",
        flush=True,
    )
    print(
        f"Noise dataset: {noise_name}",
        flush=True,
    )

    print(
        f"Pan angle: {pan_angle:.2f}",
        flush=True,
    )
    print("=" * 70, flush=True)

    recording_name = speech_file.stem

    final_output = (
        output_folder
        / f"{recording_name}.wav"
    )

    partial_output = (
        output_folder
        / f"{recording_name}.partial.wav"
    )

    metadata_file = (
        output_folder
        / f"{recording_name}-metadata.json"
    )

    prepared_audio = None
    record_process = None
    recording_completed = False

    try:
        prepared_audio = prepare_audio(
            speech_source=speech_file,
            noise_source=noise_file,
            item_number=item_number,
        )

        print(
            f"Playback duration: "
            f"{prepared_audio['duration']:.2f} seconds",
            flush=True,
        )

        record_process = start_recording(
            partial_output
        )

        time.sleep(PRE_RECORDING_TIME)

        if record_process.poll() is not None:
            raise RuntimeError(
                "The recording process stopped immediately."
            )


        play_stereo_file(
            prepared_audio["stereo_temp"]
        )
        
        time.sleep(POST_RECORDING_TIME)

        record_return_code = (
            record_process.poll()
        )

        if record_return_code is not None:
            raise RuntimeError(
                f"arecord stopped unexpectedly "
                f"with return code "
                f"{record_return_code}"
            )

        recording_completed = True


    except (Exception, KeyboardInterrupt):
        raise

    finally:
        if record_process is not None:
            stop_recording(record_process)

        remove_temporary_files(item_number)

        if not recording_completed:
            if partial_output.exists():
                partial_output.unlink()

    if not partial_output.exists():
        raise RuntimeError(
            f"Recording file was not created: "
            f"{partial_output}"
        )
        
    
    validate_recording(partial_output,prepared_audio["duration"],)

    partial_output.replace(final_output)

    file_size = final_output.stat().st_size
    recorded_duration = get_audio_duration(
        final_output
    )

    print(
        f"Saved: {final_output}",
        flush=True,
    )

    print(
        f"Recorded duration: "
        f"{recorded_duration:.2f} seconds",
        flush=True,
    )

    print(
        f"File size: {file_size} bytes",
        flush=True,
    )

    write_metadata(
        metadata_file=metadata_file,
        speech_file=speech_file,
        transcript=transcript,
        noise_name=noise_name,
        stepper1_angle=stepper1_angle,
        stepper2_angle=stepper2_angle,
        pan_angle=pan_angle,
    )

def add_recording_issue(
    recording_arguments,
    attempt_errors,
    final_status,
):
    speech_file = recording_arguments[
        "speech_file"
    ]

    issue = {
        "speech_file": speech_file.name,
        "recording_id": speech_file.stem,
        "noise_file": recording_arguments[
            "noise_file"
        ].name,
        "pan_angle": float(
            recording_arguments["pan_angle"]
        ),
        "stepper_1_angle": (
            None
            if recording_arguments["stepper1_angle"] is None
            else float(
                recording_arguments["stepper1_angle"]
            )
        ),
        "stepper_2_angle": (
            None
            if recording_arguments["stepper2_angle"] is None
            else float(
                recording_arguments["stepper2_angle"]
            )
        ),
        "failed_attempts": len(
            attempt_errors
        ),
        "final_status": final_status,
        "attempt_errors": attempt_errors,
    }

    RECORDING_ISSUES.append(
        issue
    )
    
def record_one_file_with_retry(
    **recording_arguments,
):
    attempt_errors = []

    for attempt in range(
        1,
        RECORDING_RETRIES + 1,
    ):
        try:
            result = record_one_file(
                **recording_arguments
            )

            if attempt_errors:
                add_recording_issue(
                    recording_arguments,
                    attempt_errors,
                    "recovered",
                )

            return result

        except KeyboardInterrupt:
            raise

        except Exception as error:
            attempt_errors.append(
                {
                    "attempt": attempt,
                    "error": str(error),
                    "time": datetime.now()
                    .astimezone()
                    .isoformat(),
                }
            )

            print(
                f"Recording attempt "
                f"{attempt}/"
                f"{RECORDING_RETRIES} "
                f"failed: {error}",
                flush=True,
            )

            if attempt == RECORDING_RETRIES:
                add_recording_issue(
                    recording_arguments,
                    attempt_errors,
                    "failed",
                )

                raise

            time.sleep(
                RECORDING_RETRY_DELAY
            )
            
def transfer_batch_folder(batch_folder):
    remote_target = (
        f"{WINDOWS_USER}@{WINDOWS_HOST}:"
        f"{WINDOWS_RECORDING_DIR}/"
    )

    command = [
        "scp",
        "-r",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        str(batch_folder),
        remote_target,
    ]

    for attempt in range(
        1,
        TRANSFER_RETRIES + 1,
    ):
        print(
            f"Batch transfer attempt "
            f"{attempt}/{TRANSFER_RETRIES}: "
            f"{batch_folder.name}",
            flush=True,
        )

        try:
            run_checked(command)

            print(
                f"Batch transfer completed: "
                f"{batch_folder.name}",
                flush=True,
            )

            if DELETE_AFTER_TRANSFER:
                shutil.rmtree(batch_folder)

                print(
                    f"Local batch deleted: "
                    f"{batch_folder}",
                    flush=True,
                )

            return

        except KeyboardInterrupt:
            print(
                "Batch transfer interrupted. "
                "The local batch was preserved.",
                flush=True,
            )
            raise

        except subprocess.CalledProcessError as error:
            print(
                f"Batch transfer failed with "
                f"return code {error.returncode}.",
                flush=True,
            )

            if attempt < TRANSFER_RETRIES:
                print(
                    f"Retrying in "
                    f"{TRANSFER_RETRY_DELAY} seconds.",
                    flush=True,
                )

                time.sleep(
                    TRANSFER_RETRY_DELAY
                )

    raise RuntimeError(
        f"Batch transfer failed after "
        f"{TRANSFER_RETRIES} attempts. "
        f"The local folder was preserved: "
        f"{batch_folder}"
    )


def wait_for_start_signal():
    print("", flush=True)
    print(
        "System ready. Press Enter to start.",
        flush=True,
    )

    input()

def record_clean_database(
    stepper1_angle,
    stepper2_angle,
    pan_angle,
):
    TEMP_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not SPEECH_ROOT.exists():
        raise FileNotFoundError(
            f"Speech directory not found: "
            f"{SPEECH_ROOT}"
        )

    if not NOISE_ROOT.exists():
        raise FileNotFoundError(
            f"Noise directory not found: "
            f"{NOISE_ROOT}"
        )

    if not TRANSCRIPT_FILE.exists():
        raise FileNotFoundError(
            f"Transcript file not found: "
            f"{TRANSCRIPT_FILE}"
        )

    speech_files = get_audio_files(
        SPEECH_ROOT
    )

    noise_files = get_audio_files(
        NOISE_ROOT
    )

    if not speech_files:
        raise RuntimeError(
            f"No speech files found in "
            f"{SPEECH_ROOT}"
        )

    if not noise_files:
        raise RuntimeError(
            f"No noise files found in "
            f"{NOISE_ROOT}"
        )

    transcripts = load_transcripts()

    missing_transcripts = [
        speech_file.stem
        for speech_file in speech_files
        if speech_file.stem
        not in transcripts
    ]

    if missing_transcripts:
        raise RuntimeError(
            "Missing transcripts for: "
            + ", ".join(
                missing_transcripts
            )
        )

    noise_name = get_noise_dataset_name()

    condition_folder = (
        create_condition_folder(
            noise_name=noise_name,
            pan_angle=pan_angle,
            stepper1_angle=stepper1_angle,
            stepper2_angle=stepper2_angle,
        )
    )
    
    warm_up_recording_device()
    

    print("", flush=True)
    print("=" * 70, flush=True)

    print(
        f"Speech files found: "
        f"{len(speech_files)}",
        flush=True,
    )

    print(
        f"Noise files found: "
        f"{len(noise_files)}",
        flush=True,
    )

    print(
        f"Transcripts found: "
        f"{len(transcripts)}",
        flush=True,
    )

    print(
        f"Noise dataset: "
        f"{noise_name}",
        flush=True,
    )

    print(
        f"Microphone angle: "
        f"{pan_angle:.2f}",
        flush=True,
    )


    print(
        f"Condition folder: "
        f"{condition_folder}",
        flush=True,
    )

    print("=" * 70, flush=True)

    try:
        for item_number, speech_file in enumerate(
            speech_files,
            start=1,
        ):
            noise_index = (
                item_number - 1
            ) % len(noise_files)

            noise_file = noise_files[
                noise_index
            ]

            recording_id = (
                speech_file.stem
            )

            transcript = transcripts[
                recording_id
            ]

            record_one_file_with_retry(
                speech_file=speech_file,
                transcript=transcript,
                noise_file=noise_file,
                noise_name=noise_name,
                output_folder=condition_folder,
                item_number=item_number,
                total_items=len(speech_files),
                stepper1_angle=stepper1_angle,
                stepper2_angle=stepper2_angle,
                pan_angle=pan_angle,
            )

        print("", flush=True)

        print(
            "All recordings completed.",
            flush=True,
        )

        transfer_condition_folder(
            condition_folder
        )

        print(
            "All operations completed successfully.",
            flush=True,
        )

    except KeyboardInterrupt:
        print("", flush=True)

        print(
            "Recording process interrupted.",
            flush=True,
        )

        print(
            f"Completed recordings were "
            f"preserved in: "
            f"{condition_folder}",
            flush=True,
        )

        raise

    except Exception as error:
        print("", flush=True)

        print(
            f"Recording process failed: "
            f"{error}",
            flush=True,
        )

        print(
            f"Completed recordings were "
            f"preserved in: "
            f"{condition_folder}",
            flush=True,
        )

        raise


def get_folder_manifest(folder):
    return {
        str(path.relative_to(folder)):
        path.stat().st_size
        for path in folder.rglob("*")
        if path.is_file()
    }
    
   
def transfer_condition_folder_ssh(
    condition_folder,
):
    relative_parent = (
        condition_folder.parent
        .relative_to(RECORDING_ROOT)
    )

    remote_parent = (
        f"{WINDOWS_RECORDING_DIR}/"
        f"{relative_parent.as_posix()}"
    )

    remote_windows_path = (
        remote_parent.replace(
            "/",
            "\\",
        )
    )

    ssh_target = (
        f"{WINDOWS_USER}@"
        f"{WINDOWS_HOST}"
    )

    mkdir_command = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        ssh_target,
        (
            f'cmd /c if not exist '
            f'"{remote_windows_path}" '
            f'mkdir "{remote_windows_path}"'
        ),
    ]

    scp_command = [
        "scp",
        "-r",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        str(condition_folder),
        (
            f"{ssh_target}:"
            f"{remote_parent}/"
        ),
    ]

    for attempt in range(
        1,
        TRANSFER_RETRIES + 1,
    ):
        print(
            f"Transfer attempt "
            f"{attempt}/"
            f"{TRANSFER_RETRIES}",
            flush=True,
        )

        try:
            run_checked(
                mkdir_command
            )

            run_checked(
                scp_command
            )

            print(
                f"Transfer completed: "
                f"{condition_folder}",
                flush=True,
            )

            if DELETE_AFTER_TRANSFER:
                shutil.rmtree(
                    condition_folder
                )

                for parent in [
                    condition_folder.parent,
                    condition_folder
                    .parent.parent,
                ]:
                    try:
                        parent.rmdir()
                    except OSError:
                        pass

            return

        except KeyboardInterrupt:
            raise

        except subprocess.CalledProcessError:
            if attempt < TRANSFER_RETRIES:
                time.sleep(
                    TRANSFER_RETRY_DELAY
                )

    raise RuntimeError(
        f"Transfer failed. Local files "
        f"were preserved in: "
        f"{condition_folder}"
    )

def transfer_condition_folder_usb(
    condition_folder,
):
    if not USB_MOUNT_POINT.exists():
        raise RuntimeError(
            f"USB path does not exist: "
            f"{USB_MOUNT_POINT}"
        )

    if not os.path.ismount(
        USB_MOUNT_POINT
    ):
        raise RuntimeError(
            f"USB drive is not mounted: "
            f"{USB_MOUNT_POINT}"
        )

    relative_path = (
        condition_folder.relative_to(
            RECORDING_ROOT
        )
    )

    destination = (
        USB_RECORDING_ROOT
        / relative_path
    )

    temporary_destination = (
        destination.with_name(
            destination.name + ".partial"
        )
    )

    source_manifest = (
        get_folder_manifest(
            condition_folder
        )
    )

    source_size = sum(
        source_manifest.values()
    )

    free_space = shutil.disk_usage(
        USB_MOUNT_POINT
    ).free

    if free_space < source_size + 50_000_000:
        raise RuntimeError(
            f"Not enough USB space: "
            f"required {source_size} bytes, "
            f"available {free_space} bytes"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if temporary_destination.exists():
        shutil.rmtree(
            temporary_destination
        )

    print(
        f"Copying condition to USB: "
        f"{destination}",
        flush=True,
    )

    shutil.copytree(
        condition_folder,
        temporary_destination,
    )

    copied_manifest = (
        get_folder_manifest(
            temporary_destination
        )
    )

    if copied_manifest != source_manifest:
        raise RuntimeError(
            "USB copy verification failed. "
            "The local recording was preserved."
        )

    subprocess.run(
        ["sync"],
        check=True,
    )

    if destination.exists():
        shutil.rmtree(
            destination
        )

    temporary_destination.replace(
        destination
    )

    subprocess.run(
        ["sync"],
        check=True,
    )

    print(
        f"USB copy completed: "
        f"{destination}",
        flush=True,
    )

    if DELETE_AFTER_TRANSFER:
        shutil.rmtree(
            condition_folder
        )

        for parent in [
            condition_folder.parent,
            condition_folder.parent.parent,
        ]:
            try:
                parent.rmdir()
            except OSError:
                pass

        print(
            f"Local condition deleted: "
            f"{condition_folder}",
            flush=True,
        )

def transfer_condition_folder(
    condition_folder,
):
    if TRANSFER_MODE == "usb":
        transfer_condition_folder_usb(
            condition_folder
        )

    elif TRANSFER_MODE == "ssh":
        transfer_condition_folder_ssh(
            condition_folder
        )

    else:
        raise ValueError(
            f"Invalid transfer mode: "
            f"{TRANSFER_MODE}"
        )
        
def write_recording_report():
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report_file = (
        RECORDING_ROOT
        / f"recording_report_{timestamp}.json"
    )

    report = {
        "generated_at": datetime.now()
        .astimezone()
        .isoformat(),
        "problem_recording_count": len(
            RECORDING_ISSUES
        ),
        "issues": RECORDING_ISSUES,
    }

    report_file.write_text(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Recording report saved: "
        f"{report_file}",
        flush=True,
    )

    return report_file

def main():

    stepper1_angle = 90.0
    stepper2_angle = 60.0
    pan_angle = 0.0


    wait_for_start_signal()

    try:
        record_clean_database(
            stepper1_angle=stepper1_angle,
            stepper2_angle=stepper2_angle,
            pan_angle=pan_angle,
        )

    except KeyboardInterrupt:
        print("", flush=True)
        print(
            "Recording interrupted by user.",
            flush=True,
        )

    except Exception as error:
        print("", flush=True)
        print(
            f"Recording failed: {error}",
            flush=True,
        )
        raise

    finally:
        if RECORDING_ISSUES:
            write_recording_report()


if __name__ == "__main__":
    main()
