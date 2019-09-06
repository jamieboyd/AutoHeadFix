#!/bin/bash

#******************************************************************
# This script searches for auto_start_script, if found will create a cronjob as root that opens auto start script every hour
#*******************************************************************
mypath=$(sudo find / -type d -name "AutoHeadFix" | grep "AutoHeadFix";)

if [ $? -eq 0 ];
	        then
			sudo crontab -l > croninfo.txt
			(echo "0 * * * * /bin/bash $mypath/auto_start_script.sh > $mypath/auto_start_error.txt 2>&1") >> croninfo.txt
			(echo "30 * * * * /usr/bin/python3 $mypath/water_failsafe.py > $mypath/water_failsafe_error.txt 2>&1") >> croninfo.txt
			cat croninfo.txt | sudo crontab -u root -
			rm -rf croninfo.txt
		else 

			echo "unable to generate cronjob"
fi

echo $mypath
