# Assistenzsystem: Akustisches Aufnahmesystem & Mikrofon-Array

Repository für das Projekt **Assistenzsysteme (Projekt 04: Optimierung/Überarbeitung des Aufnahmesystems)** an der **Hochschule Niederrhein (HSNR)**.

---

## 📁 Repository-Struktur & Inhalte

* **[`Analyse_und_Inbetriebnahme_Aufnahmesystem.md`](Analyse_und_Inbetriebnahme_Aufnahmesystem.md)**  
  *Das zentrale Handbuch & der vollständige Inbetriebnahme-Bericht.*  
  Enthält die theoretische Systemanalyse, den detaillierten Erfahrungsbericht der Inbetriebnahme (Netzwerk, SSH, I2C, Motorsteuerung, Sound-Routing) sowie eine **reibungsfreie Schritt-für-Schritt-Anleitung** zur Bedienung des Teststands.

* **[`acoustic_rig_test_observations_nov_12_2026.txt`](acoustic_rig_test_observations_nov_12_2026.txt)**  
  *Empirisches Test- und Beobachtungsprotokoll* der sechs-stündigen Live-Messung vom 12. November 2026. Dokumentiert das Systemverhalten unter Last, Schrittverluste der Motoren, Biegung der 1,5 m Stangen und Lautsprecher-Pegelunterschiede.

* **[`Raspi-Aufnahmesystem/`](Raspi-Aufnahmesystem/)**  
  Vollständiger Dateibaum des Raspberry Pi 4 (`/home/ami`):
  * `testcode/`: Alle Python-Steuerskripte (`main.py`, `realrecord_func.py`, `stepper.py`, `stepper2.py` etc.).
  * `Pan-Tilt_HAT_code/`: Treiber und Bibliotheken für den Waveshare Pan-Tilt Servo-HAT (PCA9685).
  * `audiodaten/`: Lokale Audio-Corpora (LibriSpeech Sprachsamples, OMEETING/DEMAND Störgeräusche).
  * `.bash_history`: Exakte Befehlshistorie der Systemeinrichtung und -erprobung.

* **[`Abschlussarbeit_YuxuanLi.pdf`](Abschlussarbeit_YuxuanLi.pdf)**  
  Die ursprüngliche Bachelorarbeit von Yuxuan Li (2025): *Entwurf und Aufbau einer automatisierten Erfassungsplattform für eine Sprachdatenbank*.

* **`01_Hardware/` & `02_Software/`**  
  Ergänzende Hardware- und Softwaredokumentationen.

---

## 🚀 Schnellstart: System hochfahren & Messung starten

Eine vollständige Anleitung mit Fehlerbehebung finden Sie in **[`Analyse_und_Inbetriebnahme_Aufnahmesystem.md`](Analyse_und_Inbetriebnahme_Aufnahmesystem.md)**.

1. **Netzteil einschalten:** Labornetzteil auf **24,0 V DC / 2,5 A** einstellen (ACT DM856 Schrittmotortreiber).
2. **Raspberry Pi booten:** Eigenes 5V/3A USB-C Netzteil anschließen.
3. **WLAN Hotspot aktivieren:** Mobilen Hotspot (2,4 GHz) auf dem Windows-Laptop einschalten.
4. **Verbinden:**
   ```powershell
   ssh -4 ami@<IP_aus_Hotspot_Einstellungen>
   ```
5. **Systemprüfung:**
   ```bash
   i2cdetect -y 1 && arecord -l | grep UMA16 && aplay -l | grep Headphones
   ```
6. **Mess-Sweep starten (Hintergrund-Modus):**
   ```bash
   cd /home/ami/testcode
   nohup python3 -u main.py > sweep.log 2>&1 &
   tail -f sweep.log
   ```
