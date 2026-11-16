import subprocess

FILE_LEFT = "/home/ami/audio/Sprecher001_20250313_EinfacherBuchSatz1_BE26_mitStoergeraeusch_HintergrundGespraech_v1.wav"
FILE_RIGHT = "/home/ami/audio/raspberrypi_python_record.wav"

TMP_LEFT = "/tmp/left_mono.wav"
TMP_RIGHT = "/tmp/right_mono.wav"

AUDIO_DEVICE = "plughw:2,0"


def convert_to_mono(input_file, output_file):
    subprocess.run(
        [
            "sox",
            input_file,
            "-r", "44100",
            "-c", "1",
            "-b", "16",
            "-e", "signed-integer",
            output_file,
        ],
        check=True,
    )


def play_stereo(left_file, right_file):
    convert_to_mono(left_file, TMP_LEFT)
    convert_to_mono(right_file, TMP_RIGHT)

    subprocess.run(
        [
            "sox",
            "-M",
            TMP_LEFT,
            TMP_RIGHT,
            "-t",
            "alsa",
            AUDIO_DEVICE,
        ],
        check=True,
    )


play_stereo(FILE_LEFT, FILE_RIGHT)
