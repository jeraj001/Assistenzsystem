import subprocess

TMP_LEFT = (
    "/home/ami/audiodaten/OMEETING_16k/"
    "OMEETING/ch01.wav"
)

TMP_RIGHT = (
"/home/ami/audiodaten/dev-clean/LibriSpeech/clean-database/84-121123-0003.flac"
)

AUDIO_DEVICE = (
    "plughw:CARD=Headphones,DEV=0"
)

LEFT_VOLUME = 4.0
RIGHT_VOLUME = 1.0

subprocess.run(
    [
        "sox",
        "-M",
        "-v", str(LEFT_VOLUME),
        TMP_LEFT,
        "-v", str(RIGHT_VOLUME),
        TMP_RIGHT,
        "-t",
        "alsa",
        AUDIO_DEVICE,
    ],
    check=True,
)
