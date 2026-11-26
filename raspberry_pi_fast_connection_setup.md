# AMI Mic-Array Studio — Fast Connection & Auto-Start Setup

This guide sets up the **AMI Mic-Array Studio** dashboard on the Raspberry Pi so anyone on the same Wi-Fi network or hotspot can open it directly in a browser—without needing SSH, VS Code, or a manual terminal session.

> **⚠️ Power Note:** Powering the Raspberry Pi from a laptop USB port works while no motors are attached, but once the Pan-Tilt servos or heavy 16-channel recordings are active, switch back to a dedicated **5 V / 3 A USB-C wall adapter** to prevent brownouts or SD card corruption.

---

## How the Fast Connection Works

1. **Network Access (`--host 0.0.0.0`):** Binds Uvicorn to all network interfaces instead of `127.0.0.1`, allowing any device on the same network to connect.
2. **Auto-Start Service (`systemd`):** Runs the dashboard automatically in the background whenever the Raspberry Pi boots and restarts it automatically if it crashes.
3. **Easy Bookmark URL:** Access the dashboard from any browser on the same network at **`http://raspberrypi.local:8000`** (or `http://<PI_IP>:8000`).

---

## Step-by-Step Setup on the Raspberry Pi

Run these commands once inside the **Raspberry Pi terminal** (via SSH).

*Note: These commands assume the username is `ami` and the project folder is located at `/home/ami/mic-array-studio`. If the Pi uses a different username (such as `pi`), replace `ami` with that username.*

### 1. Set Up the Python Environment (Skip if Already Done)

```bash
cd ~/mic-array-studio
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install fastapi uvicorn websockets numpy httpx python-dotenv sounddevice
```

**Verification:** Running `which uvicorn` prints `/home/ami/mic-array-studio/.venv/bin/uvicorn`.

---

### 2. Run a Quick Network Test

Start the server manually across the local network:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Open **`http://raspberrypi.local:8000`** in a browser on your laptop. Once the dashboard loads with a green **`WS CONNECTED`** badge, return to the Pi terminal and press **`Ctrl + C`** to stop the manual test.

---

### 3. Create the `systemd` Auto-Start Service

Open a new service file in `nano`:

```bash
sudo nano /etc/systemd/system/mic-array.service
```

Paste the following configuration (do **not** use `--reload` in production):

```ini
[Unit]
Description=AMI Mic-Array Studio Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ami
WorkingDirectory=/home/ami/mic-array-studio
ExecStart=/home/ami/mic-array-studio/.venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Save and exit `nano`: press **`Ctrl + O`**, then **`Enter`**, then **`Ctrl + X`**.

**Verification:** Running `cat /etc/systemd/system/mic-array.service` displays the exact configuration above.

---

### 4. Enable and Start the Service

Reload `systemd`, enable the service on boot, and start it immediately:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mic-array.service
sudo systemctl status mic-array.service --no-pager
```

**Verification:** The status output shows **`Active: active (running)`** in green.

---

### 5. Test Without SSH

Close the SSH terminal (or reboot the Pi with `sudo reboot` and wait ~45 seconds). Then open **`http://raspberrypi.local:8000`** in Chrome, Edge, or Safari on any device connected to the same network.

**Verification:** The dashboard loads immediately and displays a green **`WS CONNECTED`** badge with no SSH or VS Code session open.

---

## Useful Maintenance Commands

* **Apply code changes after editing files:**
  ```bash
  sudo systemctl restart mic-array.service
  ```
* **Check live logs if something goes wrong:**
  ```bash
  journalctl -u mic-array.service -n 50 --no-pager
  ```
* **Stop the background server:**
  ```bash
  sudo systemctl stop mic-array.service
  ```
* **Find the Pi's IP address (if `.local` doesn't resolve):**
  ```bash
  hostname -I
  ```