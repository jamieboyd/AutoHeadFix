#!/bin/bash
DISPLAY=":0.0"
export DISPLAY

if [[ ! $(pgrep -f __main__2.py ) ]]; then
	echo "start script" > /home/pi/tmp.txt
	echo "$DISPLAY" > /home/pi/tmp.txt
	exec /usr/bin/python3 /home/pi/Desktop/AHF_setup/AutoHeadFixSetup/AutoHeadFix/__main__2.py --temp > /dev/pts/0
fi
