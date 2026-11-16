import subprocess
import argparse
import os


def record_uma16(
    output_file="uma16_python_record.wav",
    duration=10,
    device="hw:CARD=UMA16v2,DEV=0",
    channels=16,
    samplerate=48000,
    fmt="S32_LE",
):
    cmd = [
        "arecord",
        "-D", device,
        "-c", str(channels),
        "-r", str(samplerate),
        "-f", fmt,
        "-t", "wav",
        "-d", str(duration),
        output_file,
    ]

    print("Running command:")
    print(" ".join(cmd))
    print()

    subprocess.run(cmd, check=True)

    if os.path.exists(output_file):
        print()
        print(f"Saved: {output_file}")
        print("File size:", os.path.getsize(output_file), "bytes")
    else:
        print("Recording finished, but output file was not found.")


def main():
    parser = argparse.ArgumentParser(description="Record UMA-16 audio using arecord.")
    parser.add_argument("-o", "--output", default="uma16_python_record.wav")
    parser.add_argument("-d", "--duration", type=int, default=10)
    parser.add_argument("--device", default="hw:CARD=UMA16v2,DEV=0")
    parser.add_argument("-c", "--channels", type=int, default=16)
    parser.add_argument("-r", "--samplerate", type=int, default=48000)
    parser.add_argument("-f", "--format", default="S32_LE")

    args = parser.parse_args()

    record_uma16(
        output_file=args.output,
        duration=args.duration,
        device=args.device,
        channels=args.channels,
        samplerate=args.samplerate,
        fmt=args.format,
    )


if __name__ == "__main__":
    main()
