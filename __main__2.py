#! /usr/bin/python3
#-*-coding: utf-8 -*-

#library imports
import RPi.GPIO as GPIO
from RFIDTagReader import RFIDTagReader


# local files, part of AutoHeadFix
import AHF_Settings
import AHF_CageSet

KDAYSTARTHOUR =13 # when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM
kTIMEOUTSECS= 0.05 #time to sleep in each pass through loop while witing for RFID reader


"""
RFID reader object and tag need to be global so we can access them
easily from Tag-In-Range calback
"""
tagReader=None
tag =0


"""
The plan is to copy all variables from settings, user, into a single object using setattr
Main makes a task, then calls its run method
"""
class Task:
    def __init__ (self, configFile):
        """
        Initializes a Task object with cage settings and experiment settings
        """
        AHF_CageSet.load(self) # cage settings from ./AHF_Config.jsn, only 1 of these
        AHF_Settings.load (self, configFile) # experiment settings, if configFile is None, querry user
    


def main():
    """
    The main function for the AutoHeadFix program.

    It initializes or loads settings and configurations, then endlessly loops running entries and head fix trials
    Ctrl-C is used to enter a menu-driven mode where settings can be altered.
    """
    try:
        configFile = None
#        if argv.__len__() > 1:
#            configFile = argv [1]
        task = Task (configFile) 
        print ('LED pin =', task.ledPin)
    except Exception as e:
        print ('error:' + str (e))

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
