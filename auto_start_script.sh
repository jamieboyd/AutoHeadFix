#!/bin/bash
#DISPLAY=":0.0"
#export DISPLAY
#mypath=$(sudo find / -type d -name "AutoHeadFix" | grep "AutoHeadFix";)
mypath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ ! $(pgrep -f __main__2.py ) ]]; then
	echo "start script" > /home/pi/tmp.txt
	exec /usr/bin/python3 -u $mypath/__main__2.py --temp $($mypath/load_Config.sh cageid) >>/home/pi/Desktop/log.txt 2>&1
	exec /usr/bin/python3 /home/pi/Sms/Send_text.py > /home/pi/Desktop/notifier_Log.txt 2>&1
	
fi
