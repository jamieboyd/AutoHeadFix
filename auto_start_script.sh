#!/bin/bash
DISPLAY=":0.0"
export DISPLAY

if [[ ! $(pgrep -f __main__2.py ) ]]; then
	echo "start script" > /home/pi/tmp.txt
	exec /usr/bin/python3 -u /home/pi/Desktop/AHF_setup/AutoHeadFixSetup/AutoHeadFix/__main__2.py --temp >>/home/pi/Desktop/log.txt 2>&1
	exec /usr/bin/python3 /home/pi/Sms/Send_text.py > /home/pi/Desktop/notifier_Log.txt 2>&1
	
fi
