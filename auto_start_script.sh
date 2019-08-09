#!/bin/bash
DISPLAY=":0.0"
export DISPLAY

if [[ ! $(pgrep -f __main__2.py ) ]]; then
	echo "start script" > /home/pi/tmp.txt
	exec /usr/bin/python3 -u /home/pi/Desktop/AHF_setup/AutoHeadFixSetup/AutoHeadFix/__main__2.py --temp &>/home/pi/Desktop/log.txt
	exec /usr/bin/python3 /home/pi/Desktop/AHF_setup/AutoHeadFixSetup/AutoHeadFix/text_Notifier.py &> /home/pi/Desktop/notifier_Log.txt
fi
