#!/bin/bash

#******************************************************************
# This script searches for auto_start_script, if found will create a cronjob as root that opens auto start script every hour
#*******************************************************************
mypath=$(sudo find / -type f -name "auto_start_script.sh" | grep "auto_start_script.sh";)

if [ $? -eq 0 ];
	        then
			(echo "0 * * * * /bin/bash $mypath") > croninfo.txt
			sudo crontab -l -u root | cat - croninfo.txt | sudo crontab -u root -
		else 

			echo "unable to generate cronjob"
fi

echo $mypath
