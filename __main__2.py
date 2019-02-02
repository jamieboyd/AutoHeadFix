#! /usr/bin/python3
#-*-coding: utf-8 -*-

from time import time, localtime,timezone, sleep
from datetime import datetime, timedelta

# Task configures and controls sub-tasks for hardware and stimulators
from AHF_Task import AHF_Task

"""
when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM. We close the text files
and open new ones for the day.
"""
kDAYSTARTHOUR =19

"""
constant for time outs when waiting on an event - instead of waiting for ever, and missing, e.g., keyboard event,
or callling sleep and maybe missing the thing we were waiting for, we loop using wait_for_edge with a timeout
"""
kTIMEOUTSECS = 50e-03


def main():
    """
    The main function for the AutoHeadFix program.

    It initializes or loads settings and configurations, then endlessly loops running entries and head fix trials
    Ctrl-C is used to enter a menu-driven mode where settings can be altered.
    """
    try:
        configFile = ''
        if argv.__len__() > 1:
            task = Task (argv [1])
        else:
            task = Task ('')
            task.editSettings ()
        task.setup ()
    except Exception as e:
        print ('Error initializing hardware' + str (e))
        raise e
    assert (hasattr (task, 'BrainLightClass')) # quick debug check that task got loaded

    TagReader = task.TagReader
    
    # calculate time for saving files for each day
    now = datetime.fromtimestamp (int (time()))
    nextDay = datetime (now.year, now.month, now.day, KDAYSTARTHOUR,0,0) + timedelta (hours=24)
    # Loop with a brief sleep, waiting for a tag to be read.
        while True:
            try:
                print ('Waiting for a mouse....')
                while task.TagReader.readTag == 0:
                    sleep (kTIMEOUTSECS)
                    if datetime.fromtimestamp (int (time())) > nextDay:
                        newDay (task)
                # a Tag has been read
                thisMouse = mice.getMouseFromTag (RFIDTagReader.globalTag)
                entryTime = time()
                # log entrance and give entrance reward, if this mouse supports it
                thisMouse.entry(rewarder, dataLogger)
                # set head fixing probability
                task.doHeadFix = expSettings.propHeadFix > random()
                while GPIO.input (task.tirPin)== GPIO.HIGH and time () < entryTime + task.inChamberTimeLimit:
                    if (GPIO.input (task.contactPin)== task.noContactState):
                        GPIO.wait_for_edge (task.contactPin, task.contactEdge, timeout= kTIMEOUTmS)
                    if (GPIO.input (task.contactPin)== task.contactState):
                        runTrial (thisMouse, task, camera, rewarder, headFixer, stimulator, UDPTrigger)
                        expSettings.doHeadFix = expSettings.propHeadFix > random() # set doHeadFix for next contact

            except KeyboardInterrupt:
                GPIO.output(cageSettings.ledPin, GPIO.LOW)
                headFixer.releaseMouse()
                GPIO.output(cageSettings.rewardPin, GPIO.LOW)
                lickDetector.stop_logging () 

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
