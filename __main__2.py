#! /usr/bin/python3
#-*-coding: utf-8 -*-

from time import time, localtime,timezone, sleep
from datetime import datetime, timedelta
from sys import argv
import RPi.GPIO as GPIO
# Task configures and controls sub-tasks for hardware and stimulators
from AHF_Task import Task
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
    nextDay = datetime (now.year, now.month, now.day, kDAYSTARTHOUR,0,0) + timedelta (hours=24)
    # start TagReader and Lick Detector, the two background task things, logging
    task.Reader.startLogging ()
    if hasattr(task, 'LickDetector'):
        task.LickDetector.startLogging ()
     # Top level infinite Loop running mouse entries
    try:
        while True:
            try:
                print ('Waiting for a mouse....')
                task.ContactCheck.startLogging()
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
                settingsDict = task.Subjects.miceDict.get(str(thisTag))
                #temp
                resultsDict = {"HeadFixer": {}, "Rewarder": {}, "Stimulator": {}}
                # queue up an entrance reward, that can be countermanded if a) mouse leaves early, or b) fixes right away
                task.Rewarder.giveRewardCM('entry', resultsDict.get('Rewarder'), settingsDict.get('Rewarder'))
                doCountermand = True
                # loop through as many trials as this mouse wants to do before leaving chamber
                while task.tag == thisTag:
                    # Fix mouse - returns True if 'fixed', though that may just be a True contact check if a no-fix trial
                    fixed = task.HeadFixer.fixMouse (thisTag, resultsDict.get('HeadFixer'), settingsDict.get('HeadFixer'))
                    if fixed:
                        if doCountermand:
                            task.Rewarder.countermandReward (resultsDict.get('Rewarder'), settingsDict.get('Rewarder'))
                            doCountermand = False
                                            #temporary
                        task.Stimulator.run (-1, resultsDict.get('Stimulator'), settingsDict.get('Stimulator'))
                        task.HeadFixer.releaseMouse(thisTag)
                if doCountermand:
                    task.Rewarder.countermandReward (resultsDict.get('Rewarder'), settingsDict.get('Rewarder'))
                task.ContactCheck.stopLogging()
            except KeyboardInterrupt:
                    # tag, eventKind, eventDict, timeStamp, toShellOrFile
                    task.Stimulator.quitting()
                    task.HeadFixer.releaseMouse(task.tag)
                    task.ContactCheck.stopLogging()
                    if hasattr (task, 'LickDetector'):
                        task.LickDetector.stopLogging ()
                    inputStr = '\n************** Auto Head Fix Manager ********************\nEnter:\n'
                    inputStr += 'V to run rewarder (valve) control\n'
                    inputStr += 'H for hardware tester\n'
                    inputStr += 'A to edit Animals\' individualized settings\n'
                    inputStr += 'S to edit Stimulator settings\n'
                    inputStr += 'T to edit Task configuration\n'
                    inputStr += 'L to log a note\n'
                    inputStr += 'R to Return to head fix trials\n'
                    inputStr += 'Q to quit\n:'
                    while True:
                        event = input (inputStr)
                        if event == 'r' or event == "R":
                            if hasattr (task, 'LickDetector'):
                                task.LickDetector.startLogging ()
                            break
                        elif event == 'q' or event == 'Q':
                            return
                        elif event == 'v' or event == 'V':
                            task.Rewarder.rewardControl()
                        elif event == 'a' or event == 'A':
                            task.Subjects.subjectSettings()
                        elif event == 'h' or event == 'H':
                            task.hardwareTester ()
                        elif event == 'L' or event == 'l':
                            logEvent = {"logMsg":input ('Enter your log message\n: ')}
                            task.DataLogger.writeToLogFile (0, 'logMsg', logEvent, time(),2)
                        elif event == 'T' or event == 't':
                            if hasattr(task, "Camera"):
                                task.Camera.setdown()
                                task.BrainLight.setdown()
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
        task.Stimulator.quitting()
        #task.DataLogger.setdown()
        #GPIO.output(task.ledPin, GPIO.LOW)
        task.HeadFixer.releaseMouse(task.tag)
        #GPIO.output(task.rewardPin, GPIO.LOW)
        GPIO.cleanup()
        # task.DataLogger.writeToLogFile(task.logFP, None, 'SeshEnd')
        # task.logFP.close()
        # task.statsFP.close()
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
