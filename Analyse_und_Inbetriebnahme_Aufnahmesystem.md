# Analyse, Inbetriebnahme und Workflow-Bericht des Aufnahmesystems

> **Projekt 04: Optimierung/Überarbeitung des Aufnahmesystems**  
> Modul: **PRO + SEM Assistenzsysteme** (HSNR – Fachbereich Elektrotechnik und Informatik)  
> Autoren: Chukwuekwugo Egbuonu (Kirito077) & Team  
> Referenz: Abschlussarbeit Yuxuan Li (2025), Labor-Inbetriebnahme & Praktikum-Messungen (November 2026)

---

## Inhaltsverzeichnis

1. [Einleitung & Zielsetzung](#1-einleitung--zielsetzung)
2. [Analyse der Abschlussarbeit & Systemaufbau (Ist-Zustand)](#2-analyse-der-abschlussarbeit--systemaufbau-ist-zustand)
3. [Detaillierter Erfahrungsbericht: Der Weg zur ersten Testaufnahme](#3-detaillierter-erfahrungsbericht-der-weg-zur-ersten-testaufnahme)
   - [3.1 Stromversorgung & die "Wattage-Falle" der Schrittmotoren](#31-stromversorgung--die-wattage-falle-der-schrittmotoren)
   - [3.2 Netzwerkanbindung & Remote-Zugriff (SSH / Hotspot)](#32-netzwerkanbindung--remote-zugriff-ssh--hotspot)
   - [3.3 Paketinstallation, I2C-Bus & UMA-16 Erkennung](#33-paketinstallation-i2c-bus--uma-16-erkennung)
   - [3.4 Bereitstellung von Code & Audiodaten auf dem Raspberry Pi (SCP-Upload)](#34-bereitstellung-von-code--audiodaten-auf-dem-raspberry-pi-scp-upload)
   - [3.5 Skript-Anpassungen (Hardcoded Paths / SSH-Transfer-Modus)](#35-skript-anpassungen-hardcoded-paths--ssh-transfer-modus)
   - [3.6 Windows OpenSSH-Server & der "German Windows ACL Bug"](#36-windows-openssh-server--der-german-windows-acl-bug)
   - [3.7 Motor-Fehlersuche & Signal-Kreuztest (GPIO 16/26 vs. 20/21)](#37-motor-fehlersuche--signal-kreuztest-gpio-1626-vs-2021)
   - [3.8 Erste automatisierte Testaufnahme & Datenübertragung](#38-erste-automatisierte-testaufnahme--datenübertragung)
4. [Ergebnisse der Live-Akkustik-Messung & Analyse der Praktikum-Audiodaten](#4-ergebnisse-der-live-akkustik-messung--analyse-der-praktikum-audiodaten)
   - [4.1 Mechanische Überlastung & Stepper-Schrittverluste](#41-mechanische-überlastung--stepper-schrittverluste)
   - [4.2 Akustisches Ungleichgewicht & 50-Meter-Kabeldämpfung](#42-akustisches-ungleichgewicht--50-meter-kabeldämpfung)
   - [4.3 Akustische Auswertung der Praktikum-Aufnahmen (16-Kanal UMA-16)](#43-akustische-auswertung-der-praktikum-aufnahmen-16-kanal-uma-16)
   - [4.4 Windows OneDrive "Cloud Dehydration" Fallstrick](#44-windows-onedrive-cloud-dehydration-fallstrick)
   - [4.5 Usability & CLI-Hürden](#45-usability--cli-hürden)
5. [Reibungsfreier Leitfaden: Raspberry Pi Schnellstart-Anleitung](#5-reibungsfreier-leitfaden-raspberry-pi-schnellstart-anleitung)
   - [Schritt 1: Hardware-Verkabelung & Einschaltreihenfolge](#schritt-1-hardware-verkabelung--einschaltreihenfolge)
   - [Schritt 2: Windows OpenSSH Server Einrichtung (Einmalig)](#schritt-2-windows-openssh-server-einrichtung-einmalig)
   - [Schritt 3: PC-Vorbereitung (Mobiler Hotspot)](#schritt-3-pc-vorbereitung-mobiler-hotspot)
   - [Schritt 4: SSH-Verbindung aufbauen](#schritt-4-ssh-verbindung-aufbauen)
   - [Schritt 5: System-Gesundheitsprüfung (One-Liner)](#schritt-5-system-gesundheitsprüfung-one-liner)
   - [Schritt 6: Testlauf & automatisierter Mess-Sweep](#schritt-6-testlauf--automatisierter-mess-sweep)
6. [Fazit & Nächste Projektschritte](#6-fazit--nächste-projektschritte)

---

## 1. Einleitung & Zielsetzung

Im Rahmen des Moduls **PRO + SEM Assistenzsysteme** an der Hochschule Niederrhein befasst sich das **Projekt 04** mit der Analyse, Optimierung und Überarbeitung eines bestehenden akustischen Aufnahmesystems. Das System dient zur automatisierten Erstellung von Mehrkanal-Audiodatensätzen für Richtmikrofon- (Beamforming) und Schallquellenlokalisierungs-Algorithmen (Direction of Arrival, DOA).

Dieses Dokument fasst zwei wesentliche Phasen zusammen:
1. Die theoretische Analyse der ursprünglichen Bachelor-Abschlussarbeit von Yuxuan Li (Hardwarearchitektur, Ansteuerung, Signalfluss).
2. Die praktische Inbetriebnahme des physikalischen Teststands im Labor inklusive aller aufgetretenen Fehler, Lösungswege, Messbeobachtungen (Labor-Session vom 12.11.2026), detaillierter Pegel- und Signalanalyse der ersten erzeugten Datensätze (`praktikum/audio`) sowie einer optimierten Schritt-für-Schritt-Anleitung für nachfolgende Studierende.

---

## 2. Analyse der Abschlussarbeit & Systemaufbau (Ist-Zustand)

Das Aufnahmesystem von Yuxuan Li wurde konzipiert, um reproduzierbare Testbedingungen mit definierten Winkeln zwischen Schallquelle und Mikrofonarray zu schaffen:

```mermaid
flowchart TD
    subgraph Power["Spannungsversorgung"]
        NETZ["230V Netzanschluss (Mehrfachsteckdose)"]
        LAB_PSU["Labornetzteil (24-32V DC, Doppelkanal)"]
        WALL_PI["5V / 3A USB-C Netzteil"]
        NETZ --> LAB_PSU
        NETZ --> WALL_PI
    end

    subgraph Center["Zentrale Messeinheit"]
        RPI["Raspberry Pi 4 (Linux / ALSA / Python)"]
        HAT["Waveshare Pan-Tilt HAT (PCA9685 I2C 0x40)"]
        UMA["miniDSP UMA-16 v2 (16-Kanal USB MEMS Array)"]
        WALL_PI --> RPI
        RPI --> HAT
        RPI <--> |USB 2.0| UMA
    end

    subgraph Drive["Aktorik & Schallquellen"]
        DM1["ACT DM856 Treiber 1"]
        DM2["ACT DM856 Treiber 2"]
        MOT1["Schrittmotor 1 (Wagen Links, 120° Bereich)"]
        MOT2["Schrittmotor 2 (Wagen Rechts, 120° Bereich)"]
        SPK_A["Aktiver Lautsprecher (Target Speech)"]
        SPK_P["Passiver Lautsprecher (Noise)"]
        LAB_PSU --> DM1
        LAB_PSU --> DM2
        DM1 --> MOT1
        DM2 --> MOT2
        RPI --> |GPIO 16/26| DM1
        RPI --> |GPIO 20/21| DM2
        RPI --> |3.5mm Klinke L/R| SPK_A
        SPK_A --> |50m Lautsprecherkabel (Problem)| SPK_P
    end

    HOST["Windows Steuerungs-PC"] <--> |WLAN / SSH / SCP| RPI
```

### Komponenten-Spezifikationen:
* **Zentraler Rechner:** Raspberry Pi 4 Model B (4 GB RAM), Raspberry Pi OS (Debian 13 Trixie / Kernel 6.18.50 aarch64).
* **Mikrofon-Array:** miniDSP UMA-16 v2 (16 synchron abgetastete MEMS-Mikrofone, USB-Audio Class 2.0, Abtastrate 48 kHz / 32-bit Integer S32_LE). Bekannte Hardware-Anomalie: Mikrofonkanal 10 weist erhöhtes Eigenrauschen auf.
* **Array-Orientierung:** Waveshare Pan-Tilt HAT (zwei Servos für Pan/Tilt über PCA9685 PWM-Treiber, angesteuert via I2C Bus 1 auf Adresse `0x40`).
* **Positionierungsantrieb:** 2× ACT Motor DM856 digitale Schrittmotortreiber, speisen zwei Schrittmotoren, die über 1,5 m lange Aluminiumstangen zwei fahrbare Lautsprecherwagen auf einer Kreisbahn führen (1600 Impulse pro Umdrehung = 1/8 Mikroschrittbetrieb).
* **Audio-Wiedergabe:** 3,5 mm Klinkenausgang des Raspberry Pi (bcm2835 Headphones). Kanal Links = Zielsprecher (LibriSpeech), Kanal Rechts = Störgeräusch (OMEETING).

---

## 3. Detaillierter Erfahrungsbericht: Der Weg zur ersten Testaufnahme

Die praktische Inbetriebnahme erforderte das Lösen mehrerer hardware- und softwareseitiger Hürden. Hier ist die detaillierte Chronologie:

### 3.1 Stromversorgung & die "Wattage-Falle" der Schrittmotoren
* **Problem:** Beim ersten Einschalten des Labornetzteils schaltete das Netzteil ab oder begrenzte die Spannung ("Max Wattage erreicht"), als versucht wurde, 32 V und 5 A gleichzeitig einzustellen.
* **Ursache & physikalische Erklärung:** Die ACT DM856 Treiber sind **Chopper-Schaltregler**. Sie wandeln die hohe Eingangsspannung (24–80 V) mit hohem Wirkungsgrad in die für die Motorwicklungen nötige Phasenspannung um. Ein Motor mit 4,2 A Phasenstrom benötigt pro Phase im Stillstand/langsamen Lauf nur ca. 15–30 W. Das Labornetzteil liefert bei 32 V und 2 Motoren im Normalbetrieb weniger als 1,0 bis 1,5 A pro Kanal. Die Einstellung von 32 V × 5 A = 160 W pro Kanal überlastete die Gesamtwattage-Begrenzung des Netzteil-Trafos.
* **Lösung:** 
  1. Netzteil-Ausgänge trennen.
  2. Spannung im CV-Modus (Constant Voltage) auf **24,0 V bis 28,0 V** einstellen.
  3. Strombegrenzung (CC) als Sicherheitsdecke auf **2,5 A bis 3,0 A** pro Kanal setzen.
  4. Die Schrittmotortreiber bleiben stabil im CV-Modus bei ca. 0,2–0,8 A Leerlaufruhestrom (Halbstrom-Absenkung aktiv).
  5. Der Raspberry Pi wird **niemals** über das Motornetzteil versorgt, sondern über sein eigenes 5V/3A USB-C Netzteil.

### 3.2 Netzwerkanbindung & Remote-Zugriff (SSH / Hotspot)
* **Problem:** Der Raspberry Pi sollte "Headless" (ohne Monitor/Tastatur) im Hochschullabor betrieben werden. Versuche, den Pi über das Universitäts-WLAN (eduroam / HSNR) zu verbinden, scheiterten an der 802.1X Enterprise-Authentifizierung und Client-Isolation. Zudem schlug die Namensauflösung via `raspberrypi.local` fehl, und SSH-Verbindungen brachen nach wenigen Minuten Inaktivität ab (`client_loop: send disconnect: Connection reset`).
* **Fehlersuche & Lösungsschritte:**
  1. **Mobiler Hotspot:** Einrichtung eines 2,4 GHz Hotspots direkt auf dem Windows-Laptop (IP-Bereich: `192.168.137.x`).
  2. **IPv6 Link-Local Timeout:** Windows versuchte oft, `raspberrypi.local` über IPv6 (`fe80::da3a:ddff:fe54:2b14%21`) aufzulösen, was in Timeouts endete. Lösung: Explizites Erzwingen von IPv4 mit `ssh -4 ami@raspberrypi.local` bzw. direkte Verwendung der numerischen IP aus den Windows-Hotspot-Einstellungen (`ssh ami@192.168.137.246`).
  3. **WLAN-Energiesparmodus deaktiviert:** Der Pi schaltete im Leerlauf das WLAN-Modul ab. Dauerhafte Deaktivierung über NetworkManager:
     ```bash
     sudo tee /etc/NetworkManager/conf.d/wifi-powersave.conf << 'EOF'
     [connection]
     wifi.powersave = 2
     EOF
     sudo systemctl restart NetworkManager
     ```

### 3.3 Paketinstallation, I2C-Bus & UMA-16 Erkennung
* **I2C Aktivierung:** Für den Waveshare Pan-Tilt HAT musste der I2C-Bus aktiviert werden:
  ```bash
  sudo raspi-config nonint do_i2c 0
  ```
  Prüfung via `i2cdetect -y 1` zeigte erfolgreich die Adresse `0x40` (PCA9685 PWM Servo-Controller) und `0x29` (TSL2581 Lichtsensor).
* **System-Pakete & Audio-Stack:**
  ```bash
  sudo apt update && sudo apt install -y sox libsox-fmt-all ffmpeg i2c-tools python3-pip python3-smbus python3-smbus2 python3-gpiozero python3-soundfile python3-numpy libportaudio2
  ```
* **Python-Paket-Konflikt (PEP 668):** Bei Debian Trixie existierte kein `python3-sounddevice` Paket im apt-Repository, und globales `pip install` wird durch Debian blockiert.
  Lösung: Gezielte Installation mit `--break-system-packages`:
  ```bash
  pip3 install --break-system-packages sounddevice
  ```
* **UMA-16 Hardware-Erkennung:**
  `arecord -l` bestätigte die Karte als `card 3: UMA16v2 [UMA16v2], device 0: USB Audio`.
  Testaufnahme mit `arecord -D hw:CARD=UMA16v2,DEV=0 -c 16 -r 48000 -f S32_LE test.wav` funktionierte einwandfrei.

### 3.4 Bereitstellung von Code & Audiodaten auf dem Raspberry Pi (SCP-Upload)
Da das Altsystem neu aufgesetzt wurde, mussten der Quellcode und die Audio-Stimuli vom Entwicklungsrechner auf den Pi übertragen werden:
```powershell
# Upload des Steuerungscodes
scp -r "C:\path\to\raspi-aufnahmesystem\ami\testcode" "C:\path\to\raspi-aufnahmesystem\ami\Pan-Tilt_HAT_code" ami@192.168.137.246:/home/ami/

# Upload des Audiodaten-Korpus (LibriSpeech Sprache & OMEETING Störgeräusche)
scp -r "C:\path\to\raspi-aufnahmesystem\ami\audiodaten" ami@192.168.137.246:/home/ami/
```

### 3.5 Skript-Anpassungen (Hardcoded Paths / SSH-Transfer-Modus)
In den Skripten des Vorautors (`main.py`, `realrecord_func.py`, `realrecord.py`) waren Pfade, Benutzernamen und IP-Adressen fest einprogrammiert:
* Altes System: `WINDOWS_USER = "lestileli"`, `WINDOWS_HOST = "192.168.200.220"`, `TRANSFER_MODE = "usb"` (Yuxuan Li nutzte einen USB-Stick unter `/media/ami/TPU301`).
* Automatisierte Bereinigung direkt auf dem Raspberry Pi per Python-Einzeiler:
  ```bash
  cp ~/testcode/realrecord_func.py ~/testcode/realrecord_func.py.bak && python3 -c '
  p = "/home/ami/testcode/realrecord_func.py"
  txt = open(p).read()
  txt = txt.replace("WINDOWS_USER = \"lestileli\"", "WINDOWS_USER = \"ekwug\"")
  txt = txt.replace("WINDOWS_HOST = \"192.168.200.220\"", "WINDOWS_HOST = \"192.168.137.1\"")
  txt = txt.replace("TRANSFER_MODE = \"usb\"", "TRANSFER_MODE = \"ssh\"")
  open(p, "w").write(txt)
  '
  ```
* Ebenso für `realrecord.py`:
  ```bash
  cp ~/testcode/realrecord.py ~/testcode/realrecord.py.bak && python3 -c '
  p = "/home/ami/testcode/realrecord.py"
  txt = open(p).read()
  txt = txt.replace("WINDOWS_USER = \"lestileli\"", "WINDOWS_USER = \"ekwug\"")
  txt = txt.replace("WINDOWS_HOST = \"192.168.200.220\"", "WINDOWS_HOST = \"192.168.137.1\"")
  open(p, "w").write(txt)
  '
  ```
* Zielordner auf Windows: `Desktop/praktikum/audio/recordings`.
* Option `DELETE_AFTER_TRANSFER = True` aktiviert, um den Speicherplatz der SD-Karte nach erfolgreichem SCP-Transfer automatisch zu schonen.

### 3.6 Windows OpenSSH-Server & der "German Windows ACL Bug"
Damit der Raspberry Pi nach jedem Messdurchlauf die Audio-Dateien und JSON-Metadaten vollautomatisch via `scp -o BatchMode=yes` auf den Windows-PC schieben kann, musste auf Windows der native OpenSSH-Server eingerichtet werden:

1. **OpenSSH Server installieren & Firewall-Regel anlegen (PowerShell als Admin):**
   ```powershell
   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
   Start-Service sshd
   Set-Service -Name sshd -StartupType 'Automatic'
   New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -ErrorAction SilentlyContinue
   ```

2. **Schlüsselpaar auf Pi erzeugen:**
   ```bash
   ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
   cat ~/.ssh/id_ed25519.pub
   # Ausgabe: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFCsSC58K9X3xZ7P21a9TjptBrbUh3MWL/dUDuUPauoo ami@raspberrypi
   ```

3. **Der "German Windows ACL Bug" & Lösung:**
   Auf deutschen Windows-Installationen führt der Befehl `icacls ... /grant "Administrators:F"` zu folgendem Fehler:
   > *Administrators: Zuordnungen von Kontennamen und Sicherheitskennungen wurden nicht durchgeführt.*
   
   Windows verwirft die Schlüsseldatei anschließend wegen zu offener oder fehlerhafter Berechtigungen (`Permission denied (publickey)`).
   Die sprachunabhängige Lösung nutzt die Well-Known-SID `*S-1-5-32-544`:
   ```powershell
   $pubKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFCsSC58K9X3xZ7P21a9TjptBrbUh3MWL/dUDuUPauoo ami@raspberrypi"
   Set-Content -Force -Path "$env:ProgramData\ssh\administrators_authorized_keys" -Value $pubKey
   icacls.exe "$env:ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "*S-1-5-32-544:F" /grant "SYSTEM:F"
   ```

4. **Host-Key Bestätigung:**
   Vom Pi aus einmalig ausführen:
   ```bash
   ssh -o StrictHostKeyChecking=accept-new ekwug@192.168.137.1 "echo success"
   ```
   Danach läuft jeder SCP-Transfer im `BatchMode=yes` völlig lautlos ohne Passwortabfrage.

### 3.7 Motor-Fehlersuche & Signal-Kreuztest (GPIO 16/26 vs. 20/21)
* **Problem:** Beim Testen der Einzelschritt-Skripte (`python3 stepper.py` für Motor 1 und `python3 stepper2.py` für Motor 2) drehte sich nur Motor 2. Motor 1 gab keinen Mucks von sich.
* **Signal-Kreuztest:**
  1. Versorgungsspannung ausgeschaltet.
  2. Die PUL/DIR Steuerleitungen am Treiber von Motor 1 abgezogen und stattdessen an Treiber 2 angeschlossen (und umgekehrt).
  3. Beim Aufruf von `stepper2.py` bewegte sich nun der physische Motor 1!
* **Ergebnis:** Beide ACT DM856 Treiber, beide Motoren und beide Stromversorgungskanäle sind zu 100 % intakt. Der Fehler lag an einer lockeren Dupont-Steckverbindung bzw. falscher Pin-Belegung am Raspberry Pi GPIO-Header auf Pin 36 (GPIO 16) / Pin 37 (GPIO 26). Nach dem Nachdrücken und Bereinigen der Kontakte funktionierten beide Motoren.

### 3.8 Erste automatisierte Testaufnahme & Datenübertragung
Mit funktionierendem Netzwerk, SSH-Transfer und Audio-Routing wurde ein Testlauf über eine Einzelbedingung ausgeführt:
```bash
cd ~/testcode && python3 -c '
import time, main
main.ttt.initialize()
try:
    main.initialize_stepper_references()
    main.initialize_pan_reference(0)
    time.sleep(3)
    main.move_steppers_to(60, 60)
    main.record_current_condition(90, 60, 60)
    print("Single-condition test sweep completed cleanly!", flush=True)
finally:
    main.ttt.cleanup(return_to_initial=False)
'
```

* **Signalfluss bei der Messung:**
  1. **Warmup:** UMA-16 wird 2 Sekunden warmgelaufen (`arecord -D hw:CARD=UMA16v2,DEV=0 -c 16 -r 48000 -f S32_LE -t raw -d 2 /dev/null`).
  2. **SoX Mixdown:**
     - Sprache: LibriSpeech `.flac` gewandelt zu 44.1 kHz, 16-bit Mono (`/dev/shm/clean_recording/0001_speech.wav`).
     - Rauschen: OMEETING `ch01.wav` auf Sprachlänge getrimmt (`/dev/shm/clean_recording/0001_noise.wav`).
     - Stereo-Zusammenführung: `sox -M -v 0.4 noise.wav -v 1.0 speech.wav -r 44100 -c 2 -b 16 stereo.wav`.
  3. **Synchrone Wiedergabe & Aufnahme:**
     - Wiedergabe via `aplay -D plughw:CARD=Headphones,DEV=0 --buffer-time=1000000 --period-time=200000 stereo.wav`.
     - 16-Kanal-Aufnahme via `arecord --fatal-errors -D hw:CARD=UMA16v2,DEV=0 -c 16 -r 48000 -f S32_LE -t wav ... partial.wav`.
  4. **Automatischer Transfer:**
     - Ordnererstellung auf Windows via SSH: `ssh ... cmd /c if not exist ... mkdir ...`.
     - Dateiübertragung via `scp -r ... ekwug@192.168.137.1:Desktop/praktikum/audio/recordings/...`.
     - Automatische lokale Bereinigung auf dem Pi.

---

## 4. Ergebnisse der Live-Akkustik-Messung & Analyse der Praktikum-Audiodaten

### 4.1 Mechanische Überlastung & Stepper-Schrittverluste
* **Beobachtung:** Beim Versuch, den 30°-Sweep (90° -> 60°) unter Last zu fahren, blockierten die Schrittmotoren mit lautem Rattern (Schrittverlust). Die Lautsprecherwagen bewegten sich lediglich um 10 bis 20 mm statt des geforderten Kreisbogens von über 75 cm!
* **Ursachenanalyse:**
  1. **Biegung der 1,5 m Hebelarme:** Die Schrittmotoren sitzen im Zentrum und treiben 1,5 Meter lange Aluminiumrohre an. Unter Last biegen sich die Rohre in der Mitte sichtbar durch. Das Drehmoment wird nicht steif auf die Räder übertragen.
  2. **Hohe Roll- und Haftreibung auf Teppich:** Der Versuchsraum besitzt einen Teppichboden. Die kleinen Rollen der Lautsprecherwagen sinken leicht ein. Die Haftreibung übersteigt zusammen mit dem Biegemoment der Stangen das Haltemoment der Schrittmotoren bei weitem.
  3. **12 V vs. 24 V:** Das Netzteil lieferte zeitweise nur 12 V an die Treiber. Bei 12 V sinkt die Drehmomentkurve von Schrittmotoren bei höheren Schrittfrequenzen drastisch ab.

### 4.2 Akustisches Ungleichgewicht & 50-Meter-Kabeldämpfung
* **Beobachtung:** Der aktive Hauptlautsprecher (L) war deutlich lauter als der passive Sekundärlautsprecher (R).
* **Ursachenanalyse:**
  * Obwohl der Versuchsaufbau einen Durchmesser von lediglich 3 bis maximal 5 Metern hat, ist zwischen dem primären und sekundären Lautsprecher ein **schätzungsweise 30 bis 50 Meter langes Lautsprecherkabel** aufgewickelt und verlegt!
  * Der ohmsche Leitungswiderstand und die induktive Dämpfung dieser extremen Kabelschleife vernichten einen Großteil der Audioleistung für den passiven Lautsprecher.

### 4.3 Akustische Auswertung der Praktikum-Aufnahmen (16-Kanal UMA-16)
Die bei den Tests erzeugten Originalaufnahmen im Ordner `docs/praktikum/audio/recordings/noise_normalized--32LUFS/mic_p000` wurden einer quantitativen Signal- und Pegelanalyse unterzogen:

| Messdatei | Bedingung (S1 / S2 / Pan) | Dauer | Peak (dBFS) | Mean RMS (dBFS) | Kanal 10 RMS (dBFS) | Mittlere SNR (dB) |
|---|---|---|---|---|---|---|
| `1272-128104-0000.wav` | S1: 90.0° / S2: 60.0° / Pan: 0° | 6.60 s | -60.8 | -77.2 | -77.5 | ~ -1.5 (Rauschen dominiert) |
| `1272-128104-0001.wav` | S1: 90.0° / S2: 60.0° / Pan: 0° | 5.60 s | -32.8 | -76.4 | -76.0 | +0.8 |
| `1272-128104-0002.wav` | S1: 90.0° / S2: 60.0° / Pan: 0° | 13.20 s | -31.9 | -75.8 | -74.8 | +2.0 |
| `1272-128104-0000.wav` | S1: 60.1° / S2: 60.1° / Pan: 0° | 6.60 s | -31.9 | -81.6 | -82.0 | +2.0 |
| `1272-128104-0001.wav` | S1: 60.1° / S2: 60.1° / Pan: 0° | 5.60 s | -32.0 | -76.5 | -76.6 | +5.5 |
| `1272-128104-0002.wav` | S1: 60.1° / S2: 60.1° / Pan: 0° | 13.20 s | -32.0 | -80.9 | -80.1 | +2.2 |

#### Erkenntnisse aus den Audiodaten:
1. **Niedriger Gesamtpegel:** Der RMS-Pegel liegt mit -76 dBFS bis -81 dBFS extrem niedrig. Der Dynamikbereich des 32-Bit-Wandlers wird nur minimal ausgenutzt. Ursache ist der geringe analoge Ausgangspegel des Raspberry Pi Kopfhörerausgangs (`bcm2835`) in Kombination mit der Dämpfung der langen Kabel.
2. **Niedriges Signal-zu-Rausch-Verhältnis (SNR):** Das gemessene SNR liegt im Mittel bei lediglich 1 bis 3 dB, da das OMEETING-Rauschen bei -32 LUFS im Dauerloop abgespielt wird und der Sprecherpegel (Volume 1.0) akustisch im Raum stark bedämpft ankommt.
3. **Räumliche Richtcharakteristik (Directivity):** In Bedingung `s1_p060_s2_p060` (Sprecher auf 60°) zeigen die dem Sprecher zugewandten Mikrofone (Kanal 1 & 2) einen Pegel von **-70.9 dBFS** (SNR +10.6 dB), während die abgewandten Mikrofone (Kanal 7 & 8) bei **-78.4 dBFS** (SNR +3.0 dB) liegen. Die Richtwirkung des Arrays bildet die Schallquellenorientierung somit trotz des niedrigen Signalpegels physikalisch korrekt ab!
4. **Bestätigung des Kanal-10-Artefakts:** Kanal 10 (Index 9) weist in allen Messungen eine systematische Abweichung von +1.0 bis +1.2 dB gegenüber dem Nachbarkanal auf, was Yuxuan Lis Feststellung eines Hardware-Rausch-Offsets auf Board-Ebene verifiziert.

### 4.4 Windows OneDrive "Cloud Dehydration" Fallstrick
* **Problem:** Beim automatisierten Auslesen der WAV-Dateien in Python schlug der Zugriff auf `1272-128104-0003.wav` und `0005.wav` mit `[Errno 22] Invalid argument` fehl.
* **Ursache:** Die Dateien lagen im OneDrive-synchronisierten Benutzerverzeichnis. Windows Storage Sense hatte die Dateien in den "Cloud-Only" Status versetzt (ReparsePoint mit Attribut `4199968` / `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`). Da der OneDrive-Hintergrunddienst temporär nicht aktiv war, quittierte das NTFS-Dateisystem jeden `read()`-Aufruf mit einem I/O-Fehler (*"The cloud file provider is not running"*).
* **Lösung:** Dauerhaftes Pinning aller Audio-Datensätze im Dateisystem über PowerShell:
  ```powershell
  cd "C:\path\to\praktikum\audio"
  attrib -u +p /s *.wav
  ```

### 4.5 Usability & CLI-Hürden
* **Beobachtung:** Die manuelle Bedienung über mehrere SSH-Terminals, manuelle Skriptaufrufe und IP-Überwachungen ist fehleranfällig, stressig und für Dritte nicht reproduzierbar.
* **Forderung:** Das System benötigt eine eigenständige grafische Benutzeroberfläche (Web-GUI / Streamlit / lokale Desktop-App), die Verbindungsstatus, Ausrichtung, Pegelanzeige und Sweep-Ausführung auf Knopfdruck bündelt.

---

## 5. Reibungsfreier Leitfaden: Raspberry Pi Schnellstart-Anleitung

Damit nachfolgende Teammitglieder oder Projektbetreuer den Prüfstand **ohne Vorkenntnisse und mit minimaler Reibung** in Betrieb nehmen können, ist folgende Schritt-für-Schritt-Prozedur einzuhalten:

### Schritt 1: Hardware-Verkabelung & Einschaltreihenfolge
1. **Zentrierung:** Grundplatte aufstellen. Sicherstellen, dass im Radius von 1,6 m um das Zentrum keine Hindernisse stehen.
2. **Kabelkontrolle:** UMA-16 Array per USB mit dem Pi verbinden. Klinkenkabel vom Pi (3,5 mm) in den aktiven Lautsprecher stecken.
3. **Lautsprecherwagen manuell ausrichten:** Bei **ausgeschaltetem** Motornetzteil beide Lautsprecherwagen von Hand exakt auf die 90°-Markierungslinie (senkrecht vor das Mikrofon-Array) schieben.
4. **Motornetzteil einschalten:**
   * Spannung: **24,0 V DC** (Kanal 1 & Kanal 2 unabhängig / INDEP).
   * Strombegrenzung: **2,5 A** pro Kanal.
   * Grüne PWR-LEDs an den DM856-Treibern leuchten; Motoren sperren nun mit Haltemoment.
5. **Raspberry Pi booten:** USB-C Netzteil in die Steckdose stecken. (Grüne LED flackert = Bootvorgang läuft).

### Schritt 2: Windows OpenSSH Server Einrichtung (Einmalig)
In PowerShell als Administrator:
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -ErrorAction SilentlyContinue

# Berechtigung für Pi-Schlüssel mit sprachunabhängiger SID setzen:
$pubKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFCsSC58K9X3xZ7P21a9TjptBrbUh3MWL/dUDuUPauoo ami@raspberrypi"
Set-Content -Force -Path "$env:ProgramData\ssh\administrators_authorized_keys" -Value $pubKey
icacls.exe "$env:ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "*S-1-5-32-544:F" /grant "SYSTEM:F"
```

### Schritt 3: PC-Vorbereitung (Mobiler Hotspot)
1. **Windows Mobiler Hotspot einschalten:**
   * `Windows-Taste + I` -> **Netzwerk und Internet** -> **Mobiler Hotspot** auf **Ein**.
   * Netzband: **2,4 GHz** (oder "Beliebig").
   * Energiesparmodus des Hotspots: **Aus**.

### Schritt 4: SSH-Verbindung aufbauen
1. In den Windows-Hotspot-Einstellungen nach ca. 60 Sekunden die zugewiesene IPv4-Adresse des Raspberry Pi ablesen (z. B. `192.168.137.246`).
2. PowerShell öffnen und verbinden:
   ```powershell
   ssh -4 ami@192.168.137.246
   # Passwort: (Standard-Projektpasswort)
   ```

### Schritt 5: System-Gesundheitsprüfung (One-Liner)
Im SSH-Terminal folgenden Einzeiler ausführen, um alle Sensoren, Aktoren und Audiointerfaces gleichzeitig zu validieren:
```bash
i2cdetect -y 1 && arecord -l | grep UMA16 && aplay -l | grep Headphones
```
* **Erwartete Ausgabe:**
  * I2C-Grid zeigt Adresse `40` (Pan-Tilt HAT).
  * `arecord` listet `card 3: UMA16v2`.
  * `aplay` listet `card 2: Headphones` (bcm2835).

### Schritt 6: Testlauf & automatisierter Mess-Sweep

#### A. Servos zentrieren & 0°-Referenz anfahren
```bash
python3 -c "import sys; sys.path.insert(0, '/home/ami/Pan-Tilt_HAT_code/RaspberryPi/Servo_Driver/python'); import ttt; ttt.initialize(); ttt.pwm.setRotationAngle(0, 90)"
```

#### B. Einen 1-Bedingungs-Testlauf durchführen (ca. 90 Sekunden)
```bash
cd /home/ami/testcode
python3 -c "import main; main.ttt.initialize(); main.initialize_stepper_references(); main.initialize_pan_reference(0); main.move_steppers_to(60, 60); main.record_current_condition(90, 60, 60); main.ttt.cleanup(return_to_initial=False)"
```
*Die Daten werden sofort aufgenommen, verifiziert und automatisch auf Ihren Windows-Desktop unter `Desktop\praktikum\audio\recordings` übertragen.*

#### C. Vollständigen 75-Bedingungen Sweep im Hintergrund ausführen (ca. 2 Stunden)
Damit ein Verbindungsabbruch des Laptops die Messung nicht abbricht, immer mit `nohup` starten:
```bash
cd /home/ami/testcode
nohup python3 -u main.py > sweep_run.log 2>&1 &
# Fortschritt live mitverfolgen:
tail -f sweep_run.log
```

---

## 6. Fazit & Nächste Projektschritte

Die Software- und Kommunikationskette (Raspberry Pi <-> UMA-16 <-> Pan-Tilt <-> Windows OpenSSH Auto-Transfer) ist **vollständig funktionsfähig und verifiziert**.

Die Prioritäten für die hardwareseitige Optimierung im Rahmen von Projekt 04 lauten:
1. **Lautsprecher-Verkabelung kürzen & Pegelanpassung:** Austausch des 50 m Kabels gegen ein 4 m langes, geschirmtes Lautsprecherkabel (mindestens 1,5 mm² Querschnitt) zur Beseitigung der Pegeldifferenz sowie Einsatz eines aktiven USB-Audio-Interfaces mit Vorverstärker anstelle der bcm2835-Klinke.
2. **Mechanische Entlastung der Schrittmotoren:**
   * Erhöhung der Versorgungsspannung auf stabile 24–32 V.
   * Entweder Versteifung der 1,5 m Stangen durch CFK-Profile / Dreiecks-Fachwerk ODER Umstellung auf aktiv angetriebene Lautsprecherwagen mit Eigenantrieb auf den Rädern.
3. **Entwicklung eines Web-Dashboards (GUI):** Ersatz der CLI-Bedienung durch ein leichtgewichtiges Browser-Interface zur visuellen Steuerung für Nicht-Programmierer.
