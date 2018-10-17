#! /usr/bin/python3
#-*-coding: utf-8 -*-

#library imports
import RPi.GPIO as GPIO

from RFIDTagReader import RFIDTagReader


# local files, part of AutoHeadFix
from AHF_Settings import AHF_Settings
from AHF_CageSet import AHF_CageSet

# when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM
KDAYSTARTHOUR =13


kTIMEOUTSECS= 0.05 #time to sleep in each pass through loop while witing for RFID reader


"""
RFID reader object and tag need to be global so we can access them
easily from Tag-In-Range calback
"""
from RFIDTagReader import RFIDTagReader

tagReader=None
tag =0



def main():
    """
    The main function for the AutoHeadFix program.

    It initializes or loads settings and configurations, then endlessly loops running entries and head fix trials
    Ctrl-C is used to enter a menu-driven mode where settings can be altered.
    """
    try:
        # load general settings for this cage, mostly hardware pinouts
        # things not expected to change often - there is only one AHFconfig.jsn file, in the enclosing folder
        cageSettings = AHF_CageSet()
        # get settings that may vary by experiment, including rewarder, camera parameters, and stimulator
        # More than one of these files can exist, and the user needs to choose one or make one
        # we will add some other  variables to expSettings so we can pass them as a single argument to functions
        # logFP, statsFP, dateStr, dayFolderPath, doHeadFix, 
        # configFile can be specified if launched from command line, eg, sudo python3 myconfig or sudo python3 AHFexp_myconfig.jsn
        configFile = None
        if argv.__len__() > 1:
            configFile = argv [1]
        expSettings = AHF_Settings (configFile)
        # nextDay starts tomorrow at KDAYSTARTHOUR
        now = datetime.fromtimestamp (int (time()))
        startTime = datetime (now.year, now.month,now.day, KDAYSTARTHOUR,0,0)
        nextDay = startTime + timedelta (hours=24)
         # initialize mice from mice config path, if possible
        mice = Mice(cageSettings, expSettings)
        makeLogFile (expSettings, cageSettings)
