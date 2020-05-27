# shadebox
This project is designed to control up to 4 110vac window shades from a raspberry pi 3 with the SequentMicrosystems.com "8-RELAYS for Raspberry Pi" Version 3.0 shield.

Physical setup:
Line Power is connected to the Normally Open (NO) terminal on each relay. (NO is used for safety reasons.)
And the motor drive wire (Red or Black wire) is connected to the COMmon (COM) terminal of numerically adjacent relays.
Shade 0:	Relay 1 and 2
Shade 1:	Relay 3 and 4
Shade 2:	Relay 5 and 6
shade 3:	Relay 7 and 8







installation:

git clone https://github.com/hbregalad/shadebox.git
cd shadebox
. venv_rpi/bin/activate


to setup:
Working on this.
sudo raspi-config 
5
p5


to run:
./shadebox.sh
