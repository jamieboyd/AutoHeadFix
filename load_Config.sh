#!/bin/bash
#This program takes in a command line argument as the element you wish to extract from config.txt
# Returns everything to the right (not including) the equal sign
mypath=$(sudo find / -type d -name "AutoHeadFix" | grep "AutoHeadFix";)

cat $mypath/config.txt | grep -i -e $1 | grep -o -e =.* | grep -o -e [^=].*
