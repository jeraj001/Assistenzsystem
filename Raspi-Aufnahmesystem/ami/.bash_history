arecord -D plughw:1,0 -f cd -t wav -d 5 test.wav
200~arecord -l
200~arecord -1
arecord -l
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 5 test.wav
ls -lh test.wav
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 1 -d 5 mono.wav
speaker-test -t sine -f 440 -c 2
aplay -l
[200~arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 30 record.wav &
[200~arecord -D plughw:3,0 -f S16_LE -r 16000 -c 1 -d 30 record.wav &
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 30 record.wav &
ffplay -nodisp -autoexit test.wav
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 30 record.wav & ffplay -nodisp -autoexit test.wav
sudo systemctl enable vncserver-x11-serviced
sudo systemctl start vncserver-x11-serviced
sudo systemctl get-default
sudo systemctl status vncserver-x11-serviced
sudo raspi-config
echo $XDG_SESSION_TYPE
sudo systemctl get-default
sudo systemctl status vncserver-x11-serviced --no-pager
scp ami@192.168.5.130:/home/ami/test.wav C:\Users\lestileli\Downloads\
scp ami@192.168.5.130:/home/ami/test.wav "C:\Users\lestileli\Downloads\"

scp ami@192.168.5.130:/home/ami/test.wav "$HOME\Downloads\"



cd $HOME\Downloads
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 30 record.wav &
ffplay -nodisp -autoexit test.wav
pactl list short sinks
pactl list cards
pactl load-module module-combine-sink sink_name=dual_test slaves=alsa_output.platform-fe00b840.mailbox.stereo-fallback,bluez_output.B4_E7_B3_52_0C_8B.1
pactl set-default-sink dual_test
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 5 record.wav
PULSE_SINK=alsa_output.platform-fe00b840.mailbox.stereo-fallback ffplay -nodisp -autoexit /home/ami/record.wav
PULSE_SINK=alsa_output.platform-fe00b840.mailbox.stereo-fallback ffplay -nodisp -autoexit /home/ami/record.wav &

PULSE_SINK=alsa_output.platform-fe00b840.mailbox.stereo-fallback ffplay -nodisp -autoexit /home/ami/new.wav & PULSE_SINK=alsa_output.platform-fe00b840.mailbox.stereo-fallback ffplay -nodisp -autoexit /home/ami/record.wav &
PULSE_SINK=bluez_output.B4_E7_B3_52_0C_8B.1 paplay /home/ami/test.wav
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 5 new.wav & PULSE_SINK=alsa_output.platform-fe00b840.mailbox.stereo-fallback ffplay -nodisp -autoexit /home/ami/record.wav &
PULSE_SINK=bluez_output.B4_E7_B3_52_0C_8B.1 paplay /home/ami/test.wav
python /home/ami/record_and_play.py
python /home/ami/dual.py
sudo apt update
sudo apt install pigpio python3-pigpio -y
python3 -c "import gpiozero; print('gpiozero ok')"
python3 -c "import lgpio; print('lgpio ok')"
python3 /home/ami/motor.py
scp ami@192.168.200.130:/home/ami/uma16_python_record.wav C:\Users\lestileli\Desktop\
exit
pip install soundfile
apt install python3-soundfile
sudo apt update
sudo apt install python3-soundfile python3-numpy
sudo apt install python3-sounddevice
lsusb
arecord -l
arecord -L
arecord -D hw:CARD=UMA16v2,DEV=0 --dump-hw-params
arecord -D hw:CARD=UMA16v2,DEV=0   -c 16   -r 48000   -f S32_LE   -t wav   -d 5   uma16_test.wav
file uma16_test.wav
sudo apt install sox
soxi uma16_test.wav
sudo raspi-config
sudo reboot
sudo apt install i2c-tools -y
i2cdetect -y 1
sudo apt-get install python3-smbus -y
sudo apt install python3-pip python3-smbus i2c-tools -y
wget https://files.waveshare.com/wiki/Pan-Tilt_HAT/Pan-Tilt_HAT_code.zip
unzip Pan-Tilt_HAT_code.zip
cd Pan-Tilt_HAT_code/RaspberryPi/
sudo apt install sox libsox-fmt-all -y
hostname
sox --version
play --version
aplay -l
speaker-test -c 2 -t wav -D plughw:2,0
AUDIODEV=plughw:2,0 play /home/ami/audio/Sprecher001_20250313_EinfacherBuchSatz1_BE26_mitStoergeraeusch_HintergrundGespraech_v1.wav
play /home/ami/audio/Sprecher001_20250313_EinfacherBuchSatz1_BE26_mitStoergeraeusch_HintergrundGespraech_v1.wav -t alsa plughw:2,0
sox /home/ami/audio/Sprecher001_20250313_EinfacherBuchSatz1_BE26_mitStoergeraeusch_HintergrundGespraech_v1.wav -t alsa plughw:2,0
sox /home/ami/audio/Sprecher001_20250313_EinfacherBuchSatz1_BE26_mitStoergeraeusch_HintergrundGespraech_v1.wav -r 44100 -c 1 -b 16 -e signed-integer /tmp/test_mono.wav
sox /tmp/test_mono.wav -t alsa plughw:2,0
aplay -l
arecord -l
speaker-test -D plughw:3,0 -c 2 -t sine
speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2 -r 44100 -t sine
journalctl --since "1 hour ago" | grep -Ei "usb|alsa|snd|audio|error|fail|xrun|disk|space|filesystem|i/o"
pgrep -a arecord
ssh lestileli@192.168.200.220
cat /home/ami/.ssh/id_ed25519.pub
netstat -ano | findstr ":22"
ping -c 4 192.168.200.220
nc -vz -w 5 192.168.200.220 22
ssh lestileli@192.168.200.220
ssh-keygen -t ed25519
cat ~/.ssh/id_ed25519.pub
ssh -o BatchMode=yes lestileli@192.168.200.220 "echo success"
echo "transfer test" > /tmp/transfer_test.txt
scp -o BatchMode=yes /tmp/transfer_test.txt lestileli@192.168.200.220:Desktop/praktikum/audio/recordings/
pgrep -a arecord
pgrep -a aplay
speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2 -r 44100 -t sine
[200~speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2 -r 44100 \
speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2 -r 44100 -t sine
amixer -c 0 scontrols
amixer -c 0
amixer -c 0 sset PCM 0dB unmute
speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2 -r 44100 -t sine
pgrep -a aplay
pgrep -a arecord
kill 4435
pgrep -a arecord
ifconfig
sudo raspi-config
lsblk -f
sudo mkdir -p /mnt/oldsd
sudo mount dev/sda2 /mnt/oldsd
sudo mkdir -p /mnt/oldsd
sudo mount /dev/sda2 /mnt/oldsd
ls /mnt/oldsd/home/ami
cp -a /mnt/oldsd/home/ami/. /home/ami/
ls -la /home/ami
sudo umount /mnt/oldsd
sudo eject /dev/sda
aplay -l
arecord -l
i2cdetect -y 1
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y sox ffmpeg git i2c-tools python3-pip python3-smbus python3-gpiozero
pip3 install smbus2
sudo apt install python3-smbus2
speaker-test -c 2
arecord -D hw:CARD=UMA16v2,DEV=0 -c 16 -r 48000 -f S32_LE test.wav
arecord
arecord -l
aplay -L
speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2
aplay -D plughw:CARD=Headphones,DEV=0 /usr/share/sounds/alsa/Front_Center.wav
ssh lestileli@192.168.200.220
scp test.txt lestileli@192.168.200.220:/C:/Users/lestileli/Desktop/
ls ~/.ssh
cat ~/.ssh/config
ssh lestileli@192.168.200.220
sync
sudo umount /media/ami/TPU301
speaker-test -D plughw:CARD=Headphones,DEV=0 -c 2 -t wav
