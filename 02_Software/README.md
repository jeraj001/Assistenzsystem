# AMI // Mic-Array Studio

Web-based control and monitoring interface for the HSNR 16-channel microphone array testbed. Built with **FastAPI + WebSockets** (backend) and **HTML/CSS/JS** (frontend), with a built-in **Simulation Mode** so the team can develop and test without needing the Raspberry Pi connected.

---

## 1. Quick Start (Simulation Mode)

Run these commands inside the `mic-array-studio` folder:

```bash
# 1. Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell

# 2. Install dependencies
pip install fastapi uvicorn websockets numpy

# 3. Start the server
uvicorn backend.app:app --reload
```

Open **`http://127.0.0.1:8000`** in your browser.

### What You Can Test in Simulation
* **Speaker 1 & 2 Controls:** Drag sliders or click presets (`0°–120°`) to move both speaker arms on the 2D radar view.
* **Mic Array Pan & Tilt:** Rotate the microphone array (`-45°` to `+45°` Pan, `-30°` to `+30°` Tilt).
* **Stepper Motor Power (`ON` / `SILENT (OFF)`):** Simulates cutting motor power during recordings to reduce motor buzz (locks speaker motion while off).
* **E-STOP:** Halts all motion and cuts motor power. To resume, click **`RESET E-STOP`** (top right) and turn **Stepper Motor Power** back **`ON`**.
* **CH10 Guard (`CH10 MUTED` / `CH10 LIVE`):** Toggles the simulated noise/spikes on Channel 10.
* **Record & Transcribe:** Simulates a recording capture and logs a timestamped test transcription with the current rig angles.

---

## 2. Top Status Bar Explained

| Badge | Meaning |
|---|---|
| **`SIMULATION MODE`** | Running locally with simulated motors and audio (switches to `LIVE PI HARDWARE` on the Raspberry Pi). |
| **`WS CONNECTED`** | **WebSocket Connected** — live two-way link between the browser UI and Python backend (20 Hz updates). |
| **`UMA-16 v2`** | Status of the 16-channel USB MEMS microphone array. |
| **`I2C PAN-TILT`** | Status of the Waveshare Pan-Tilt servo controller connected to the Pi over the **I2C** bus (controls mic array rotation). |
| **`ENCODERS: OPEN-LOOP`** | Position feedback status. Currently open-loop (counts motor steps); ready to switch to closed-loop once physical angle encoders (*Winkelgeber*) are installed. |
| **`CPU °C \| GB`** | Raspberry Pi CPU temperature and free SD card storage. |

---

## 3. How to Edit the Interface

Every part of the app is separated by file:

| File | What It Controls |
|---|---|
| `frontend/index.html` | Page layout, buttons, labels, and panels |
| `frontend/style.css` | Colors, dark theme, fonts, and visual design |
| `frontend/app.js` | Button clicks, WebSocket updates, and 2D rig canvas drawing |
| `backend/app.py` | API endpoints and WebSocket server |
| `backend/drivers/simulator.py` | Simulated motor movement, 16-ch audio levels, and mock transcription |
| `backend/drivers/hardware.py` | Real Raspberry Pi hardware driver (GPIO, I2C, ALSA) |
| `config.json` | Default settings (Pi IP, angle limits, safe park pose, mode) |

**Editing workflow:** Keep `uvicorn backend.app:app --reload` running → edit any file in VS Code → press **Save** (`Cmd+S` / `Ctrl+S`) → hard-refresh the browser (`Cmd+Shift+R` / `Ctrl+Shift+R`) to see changes instantly.
