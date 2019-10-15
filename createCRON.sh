#!/bin/bash

#******************************************************************
# This script searches for path of AutoiHeadFix folder
# if found will create  A)  cronjob as root that opens auto start script every hour
#			B) cronjob that runs water_failsafe.py every 30minutes
#			C) Cronjob that runs auto restart upon reboot of the pi
##################
#VERY IMPORTANT:YOU CANNOT HAVE MORE THAN ONE AutoHeadFix FOLDER ON YOUR MACHINE 
#*******************************************************************

#mypath=$(sudo find / -type d -name "AutoHeadFix" | grep "AutoHeadFix";)
configpath="/home/pi"

mypath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ $? -eq 0 ];
	        then
			sudo crontab -l > croninfo.txt
			(echo "0 * * * * /bin/bash $mypath/auto_start_script.sh > auto_start_error.txt 2>&1") >> croninfo.txt
			(echo "30 * * * * /usr/bin/python3 $mypath/water_failsafe.py > water_failsafe_error.txt 2>&1") >> croninfo.txt
			(echo "@reboot /bin/bash $mypath/auto_start_script.sh > reboot_error.txt 2>&1") >> croninfo.txt
			cat croninfo.txt | sudo crontab -u root -
			rm -rf croninfo.txt
		else 

			echo "unable to generate cronjob"
fi

echo $mypath
