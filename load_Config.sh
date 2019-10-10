#!/bin/bash
#This program takes in a command line argument as the element you wish to extract from config.txt
# Returns everything to the right (not including) the equal sign
#mypath=$(sudo find / -type d -name "AutoHeadFix" 2>&1 |grep -v "Permission denied" | grep "AutoHeadFix";)
DIR="/home/pi"

cat $DIR/config.txt | grep -i -e $1 | grep -o -e =.* | grep -o -e [^=].*
