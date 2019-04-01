#! /usr/bin/python3
#-*-coding: utf-8 -*-

from time import time, localtime,timezone, sleep
from datetime import datetime, timedelta

# Task configures and controls sub-tasks for hardware and stimulators
from AHF_Task import AHF_Task
# hardware tester can be called from menu pulled up by keyboard interrupt
from AHF_HardwareTester import hardwareTester

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
    assert (hasattr (task, 'BrainLight')) # quick debug check that task got loaded and setup ran
    # calculate time for saving files for each day
    now = datetime.fromtimestamp (int (time()))
    nextDay = datetime (now.year, now.month, now.day, KDAYSTARTHOUR,0,0) + timedelta (hours=24)
    # start TagReader and Lick Detector, the two background task things, logging
    task.TagReader.startLogging ()
    if hasattr(task, 'LickDetector'):
        task.LickDetector.startLogging ()
     # Top level infinite Loop running mouse entries/trials
    while True:
        try:
            print ('Waiting for a mouse....')
            # loop with a brief sleep, waiting for a tag to be read, or a new day to dawn
            while True:
                if task.tag != 0:
                    break
                else:
                    if datetime.fromtimestamp (int (time())) > nextDay:
                        task.DataLogger.newDay ()
                    else:
                        sleep (kTIMEOUTSECS)
            # a Tag has been read, get a reference to the dictionaries for this subject
            thisTag = task.tag
            subjectDict = task.Subjects.get (tag)
            resultsDict = subjectDict.get ('results')
            settingsDict = subjectDict.get ('settings')
            # queue up an entrance reward
            task.Rewarder.giveRewardCM('entry', resultsDict.get('Rewarder'), settingsDict.get('Rewarder'))
            # loop through as many trials as this mouse wants to do before leaving chamber
            while task.tag == thisTag:
                # Fixmouse, or do unfixed trial
                
            
            # set head fixing probability
            task.doHeadFix = expSettings.propHeadFix > random()
            while GPIO.input (task.tirPin)== GPIO.HIGH and time () < entryTime + task.inChamberTimeLimit:
                if (GPIO.input (task.contactPin)== task.noContactState):
                    GPIO.wait_for_edge (task.contactPin, task.contactEdge, timeout= kTIMEOUTmS)
                if (GPIO.input (task.contactPin)== task.contactState):
                    runTrial (thisMouse, task, camera, rewarder, headFixer, stimulator, UDPTrigger)
                    expSettings.doHeadFix = expSettings.propHeadFix > random() # set doHeadFix for next contact

            except KeyboardInterrupt:
                
        
        
                    
                if hasattr (task, 'LickDetector'):
                    task.lickDetector.stop_logging ()
                inputStr = '\n************** Auto Head Fix Manager ********************\nEnter:\n'
                inputStr +='V to run rewarder (valve) control\n'
                inputStr += 'H for hardware tester\n'
                inputStr += 'S to edit Stimulator settings\n'
                inputStr += 'T to edit Task configuration\n'
                inputStr += 'L to log a note\n'
                inputStr += 'R to Return to head fix trials\n'
                inputStr += 'Q to quit\n:'
                while True:
                    event = input (inputStr)
                    if event == 'r' or event == "R":
                        if hasattr (task, 'LickDetector'):
                            task.lickDetector.start_logging ()
                        break
                    elif event == 'q' or event == 'Q':
                        return
                    elif event == 'v' or event== "V":
                        task.Rewarder.rewardControl()
                    elif event == 'h' or event == 'H':
                        task.hardwareTester ()
                    elif event == 'L' or event == 'l':
                        logEvent = input ('Enter your log message\n: ')
                        task.DataLogger.logEvent (0, 'logMsg:%s' % logEvent)
                    elif event == 'T' or event == 't':
                        task.editSettings()
                        response = input ('Save edited settings to file?')
                        if response [0] == 'Y' or response [0] == 'y':
                            task.saveSettings ()
                        task.setup ()
                    elif event == 'S' or event == 's':
                        task.Stimulator.settingsDict = task.Stimulator.config_user_get (task.Stimulator.settingsDict)
                        task.Stimulator.setup()

    except Exception as anError:
        print ('Auto Head Fix error:' + str (anError))
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
