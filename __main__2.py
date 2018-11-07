#! /usr/bin/python3
#-*-coding: utf-8 -*-

#library imports
import RPi.GPIO as GPIO
import RFIDTagReader
from RFIDTagReader import RFIDTagReader
from PTCountermandPulse import CountermandPulse

# local files, part of AutoHeadFix
import AHF_Settings
import AHF_CageSet



from time import time, localtime,timezone, sleep
from datetime import datetime, timedelta

KDAYSTARTHOUR =13 # when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM
kTIMEOUTSECS= 0.05 #time to sleep in each pass through loop while witing for RFID reader


def newDay (task):
    now = datetime.fromtimestamp (int (time()))
    startTime = datetime (now.year, now.month, now.day, KDAYSTARTHOUR,0,0)
    nextDay = startTime + timedelta (hours=24)
    mice.show()
    writeToLogFile(expSettings.logFP, None, 'SeshEnd')
    expSettings.logFP.close()
    expSettings.statsFP.close()
    makeDayFolderPath(expSettings, cageSettings)
    makeLogFile (expSettings, cageSettings)
    simpleLogger.logFP = expSettings.logFP
    makeQuickStatsFile (expSettings, cageSettings, mice)
    stimulator.nextDay (expSettings.logFP)
    mice.clear ()

def main():
    """
    The main function for the AutoHeadFix program.

    It initializes or loads settings and configurations, then endlessly loops running entries and head fix trials
    Ctrl-C is used to enter a menu-driven mode where settings can be altered.
    """
    try:
        configFile = None
        if argv.__len__() > 1:
            configFile = argv [1]
        task = Task (configFile) 
        print ('LED pin =', task.ledPin) # quick debug check that task got loaded
        # initialize GPIO, and initialize pins for the simple tasks; more complex tasks have their own code for initializing
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        # set up pin that turns on brain illumination LED
        GPIO.setup (task.ledPin, GPIO.OUT, initial = GPIO.LOW)
        # set up pin for ascertaining mouse contact, ready for head fixing
        GPIO.setup (task.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + task.contactPUD))
        # set up countermandable pulse for water solenoid
        rewarder = PTCountermandPulse (task.rewardPin, 0, 0, task.entranceRewardTime, 1)
        
        # make head fixer - does its own GPIO initialization from info in task
        headFixer=AHF_HeadFixer.get_class (task.headFixer) (task)
        # set up tag reader with callback on tag_in_range_pin
        # the callback will set RFIDTagReader.globalTag
        tagReader =TagReader (task.serialPort, doChecksum = True, timeOutSecs = 0.05, kind='ID')
        tagReader.installCallBack (task.tag_in_range_pin)
        
        now = datetime.fromtimestamp (int (time()))
        startTime = datetime (now.year, now.month, now.day, KDAYSTARTHOUR,0,0)
        #set 
        # Loop with a brief sleep, waiting for a tag to be read.
        while True:
            try:
                print ('Waiting for a mouse....')
                while RFIDTagReader.globalTag == 0:
                    sleep (kTIMEOUTSECS)
                    if datetime.fromtimestamp (int (time())) > nextDay:
                        newDay (task)
                # a Tag has been read
                thisMouse = mice.getMouseFromTag (RFIDTagReader.globalTag)
                if thisMouse.entranceRewards < expSettings.maxEntryRewards:

     except Exception as anError:
        print ('AutoHeadFix error:' + str (anError))
        raise anError
    finally:
        stimulator.quitting()
        GPIO.output(task.ledPin, GPIO.LOW)
        headFixer.releaseMouse()
        GPIO.output(task.rewardPin, GPIO.LOW)
        GPIO.cleanup()
        writeToLogFile(task.logFP, None, 'SeshEnd')
        task.logFP.close()
        task.statsFP.close()
        print ('AutoHeadFix Stopped')
                

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
"""
if __name__ == '__main__':
    main()
