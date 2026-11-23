import math
import random
import time
from datetime import datetime


class RigSimulator:
    """Simulates the Raspberry Pi rig (steppers, Pan-Tilt servos, UMA-16 audio, transcription)."""

    def __init__(self, config: dict):
        self.config = config
        self.limits = config["limits"]

        # Current physical angles (degrees)
        self.speaker1 = 90.0
        self.speaker2 = 60.0
        self.pan = 0.0
        self.tilt = 0.0

        # Target angles commanded by the UI
        self.target_speaker1 = 90.0
        self.target_speaker2 = 60.0
        self.target_pan = 0.0
        self.target_tilt = 0.0

        # System states
        self.estop_active = False
        self.motor_power = True
        self.ch10_muted = config.get("channel_10_muted", True)
        self.transcribing = False
        self.t = 0.0

        # Live 16-channel dBFS values & peak hold
        self.channels_db = [-65.0] * 16
        self.peaks_db = [-65.0] * 16

        # Logs and transcriptions
        self.logs = [
            self._make_log("INFO", "Simulation engine initialized (mode: SIMULATION)."),
            self._make_log("INFO", "Hardware safety limits active: Speakers 0°-120°, Pan ±45°."),
        ]
        self.transcriptions = [
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "text": "System ready. Click 'Record & Transcribe' to test speech capture.",
                "angles": "S1: 90° | S2: 60° | Pan: 0°",
                "confidence": 98,
                "status": "ready",
            }
        ]

    def _make_log(self, level: str, msg: str) -> dict:
        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "msg": msg,
        }

    def add_log(self, level: str, msg: str):
        self.logs.insert(0, self._make_log(level, msg))
        self.logs = self.logs[:30]

    def set_target(self, axis: str, angle: float):
        if self.estop_active:
            self.add_log("WARN", "Command blocked: E-STOP is active. Reset E-STOP first.")
            return False

        if axis in ("speaker1", "speaker2"):
            if not self.motor_power:
                self.add_log("WARN", "Motors are powered off (Silent Mode). Enable motor power to move.")
                return False
            clamped = max(self.limits["speaker_min"], min(self.limits["speaker_max"], float(angle)))
            if axis == "speaker1":
                self.target_speaker1 = clamped
            else:
                self.target_speaker2 = clamped
            self.add_log("CMD", f"{axis.upper()} target set to {clamped:.1f}°")
            return True

        if axis == "pan":
            clamped = max(self.limits["pan_min"], min(self.limits["pan_max"], float(angle)))
            self.target_pan = clamped
            self.add_log("CMD", f"Mic Array PAN target set to {clamped:.1f}°")
            return True

        if axis == "tilt":
            clamped = max(self.limits["tilt_min"], min(self.limits["tilt_max"], float(angle)))
            self.target_tilt = clamped
            self.add_log("CMD", f"Mic Array TILT target set to {clamped:.1f}°")
            return True

        return False

    def set_estop(self, active: bool):
        self.estop_active = active
        if active:
            self.target_speaker1 = self.speaker1
            self.target_speaker2 = self.speaker2
            self.target_pan = self.pan
            self.target_tilt = self.tilt
            self.motor_power = False
            self.add_log("ALERT", "E-STOP TRIGGERED! All motion halted and motor power cut.")
        else:
            self.add_log("INFO", "E-STOP cleared. Re-enable motor power when ready.")

    def safe_park(self):
        if self.estop_active:
            self.add_log("WARN", "Cannot park while E-STOP is active.")
            return
        self.target_pan = float(self.config["safe_park"]["pan"])
        self.target_tilt = float(self.config["safe_park"]["tilt"])
        self.add_log("INFO", "Moving Pan-Tilt servos smoothly to Safe Park rest position (0°, 0°).")

    def home_all(self):
        if self.estop_active:
            self.add_log("WARN", "Cannot home while E-STOP is active.")
            return
        if self.motor_power:
            self.target_speaker1 = 90.0
            self.target_speaker2 = 90.0
        self.target_pan = 0.0
        self.target_tilt = 0.0
        self.add_log("INFO", "Returning rig to baseline reference (S1: 90°, S2: 90°, Array: 0°).")

    def set_motor_power(self, enabled: bool):
        if self.estop_active and enabled:
            self.add_log("WARN", "Clear E-STOP before enabling motor power.")
            return
        self.motor_power = enabled
        state_txt = "ENABLED (active hold)" if enabled else "CUT (Silent Mode - zero motor buzz)"
        self.add_log("INFO", f"Stepper driver power {state_txt}.")

    def set_ch10_mute(self, muted: bool):
        self.ch10_muted = muted
        self.add_log("INFO", f"UMA-16 Channel 10 {'muted (excluded from DSP)' if muted else 'UNMUTED (faulty capsule active)'}.")

    def _move_toward(self, current: float, target: float, speed_per_tick: float) -> float:
        diff = target - current
        if abs(diff) <= speed_per_tick:
            return target
        return current + math.copysign(speed_per_tick, diff)

    def step(self, dt: float = 0.05):
        """Advances simulated motion and 16-channel audio levels."""
        self.t += dt

        if not self.estop_active:
            if self.motor_power:
                self.speaker1 = self._move_toward(self.speaker1, self.target_speaker1, 24.0 * dt)
                self.speaker2 = self._move_toward(self.speaker2, self.target_speaker2, 24.0 * dt)
            # Smooth slow servo stepping (~20 deg/sec, mimicking thesis 1 deg / 0.05 s)
            self.pan = self._move_toward(self.pan, self.target_pan, 20.0 * dt)
            self.tilt = self._move_toward(self.tilt, self.target_tilt, 20.0 * dt)

        # Simulate realistic 16-channel UMA-16 levels (higher during transcription, subtle spatial gradient)
        base_speech = -26.0 if self.transcribing else -46.0
        buzz_floor = 4.5 if self.motor_power else 0.0
        speech_wave = 9.0 * abs(math.sin(self.t * 4.2)) * (0.5 + 0.5 * math.sin(self.t * 1.7))

        for i in range(16):
            col = i % 4
            # Slight directional gradient across the 4x4 grid based on speaker1 & pan
            angle_bias = math.cos(math.radians(self.speaker1 - self.pan)) * (col - 1.5) * 1.4
            level = base_speech + speech_wave + angle_bias + buzz_floor + random.uniform(-1.8, 1.8)

            # Channel 10 (index 9): simulate known hardware hiss/glitch
            if i == 9:
                if self.ch10_muted:
                    level = -90.0
                else:
                    level += 11.5
                    if random.random() < 0.08:
                        level = -18.0  # transient electrical spike

            level = max(-90.0, min(-1.0, level))
            self.channels_db[i] = round(level, 1)

            # Peak hold with slow decay
            if level > self.peaks_db[i]:
                self.peaks_db[i] = round(level, 1)
            else:
                self.peaks_db[i] = round(max(level, self.peaks_db[i] - 10.0 * dt), 1)

    def add_simulated_transcription(self):
        samples = [
            "Welcome to the hotel reception, how can I assist you today?",
            "Please navigate to conference room B on the second floor.",
            "Testing sixteen channel microphone array beamforming alignment.",
            "The service robot should focus on the primary speaker voice.",
        ]
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "text": random.choice(samples),
            "angles": f"S1: {self.speaker1:.1f}° | S2: {self.speaker2:.1f}° | Pan: {self.pan:.1f}°",
            "confidence": random.randint(91, 99),
            "status": "ok",
        }
        self.transcriptions.insert(0, entry)
        self.transcriptions = self.transcriptions[:12]
        self.add_log("STT", f"Transcribed audio ({entry['confidence']}% conf): \"{entry['text'][:42]}...\"")

    def get_telemetry(self) -> dict:
        moving = (
            abs(self.speaker1 - self.target_speaker1) > 0.1
            or abs(self.speaker2 - self.target_speaker2) > 0.1
            or abs(self.pan - self.target_pan) > 0.1
            or abs(self.tilt - self.target_tilt) > 0.1
        )
        active_channels = [v for idx, v in enumerate(self.channels_db) if idx != 9 or not self.ch10_muted]
        mean_rms = round(sum(active_channels) / len(active_channels), 1)

        return {
            "mode": self.config.get("mode", "simulation"),
            "pi_host": self.config.get("pi_host", "192.168.137.246"),
            "estop": self.estop_active,
            "motor_power": self.motor_power,
            "ch10_muted": self.ch10_muted,
            "moving": moving,
            "transcribing": self.transcribing,
            "angles": {
                "speaker1": round(self.speaker1, 1),
                "target_speaker1": round(self.target_speaker1, 1),
                "speaker2": round(self.speaker2, 1),
                "target_speaker2": round(self.target_speaker2, 1),
                "pan": round(self.pan, 1),
                "target_pan": round(self.target_pan, 1),
                "tilt": round(self.tilt, 1),
                "target_tilt": round(self.target_tilt, 1),
            },
            "health": {
                "uma16": True,
                "i2c_pantilt": True,
                "audio_out": True,
                "encoders": False,
                "cpu_temp": round(46.2 + math.sin(self.t * 0.2) * 1.1, 1),
                "disk_free_gb": 18.4,
            },
            "audio": {
                "channels_db": self.channels_db,
                "peaks_db": self.peaks_db,
                "mean_rms": mean_rms,
            },
            "transcriptions": self.transcriptions,
            "logs": self.logs[:12],
        }
