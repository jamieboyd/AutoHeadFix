#! /usr/bin/python3
#-*-coding: utf-8 -*-

#library imports
import RPi.GPIO as GPIO

# local files, part of AutoHeadFix
from AHF_Task import AHF_Task

"""
when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM. We close the text files
and open new ones for the day.
"""
kDAYSTARTHOUR =13

"""
constant for time outs when waiting on an event - instead of waiting for ever, and missing, e.g., keyboard event,
or callling sleep and maybe missing the thing we were waiting for, we loop using wait_for_edge with a timeout
"""
kTIMEOUTmS = 50



def main():
    """
    The main function for the AutoHeadFix program.

    It initializes or loads settings and configurations, then endlessly loops running entries and head fix trials
    Ctrl-C is used to enter a menu-driven mode where settings can be altered.
    """
    try:
        configFile = ''
        if argv.__len__() > 1:
            configFile = argv [1]
            task = Task (configFile)
        else:
            task = Task ('')
            response = input ('Edit settings loaded from %s?' % task.fileName)
            if response [0] == 'y' or response [0] == 'Y':
                task.editSettings()
                response = input ('Save new/updated settings to a task configuration file?')
                if response [0] == 'y' or response [0] == 'Y':
                    task.saveSettings ()
        assert (hasattr (task, 'LEDpin') # quick debug check that task got loaded
        # initialize GPIO, and initialize pins for the simple sub-tasks; more complex sub-tasks have their own code for initializing
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        # set up pin that turns on brain illumination LED
        GPIO.setup (task.LEDpin, GPIO.OUT, initial = GPIO.LOW)
        # set up pin for ascertaining mouse contact, ready for head fixing
        GPIO.setup (task.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, task.contactPUD))
        # set up countermandable pulse for water solenoid
        rewarder = PTCountermandPulse (task.rewardPin, 0, 0, task.entranceRewardTime, 1)
        setattr (task, 'rewarder', rewarder)
        # make head fixer - does its own GPIO initialization from info in task
        if task.hasHeadFixer:
            headFixer=AHF_HeadFixer.get_class (task.headFixerClass) (task.headFixerDict)
            setattr (task, 'headFixer', headFixer)
        # set up tag reader with callback on tag_in_range_pin
        # the callback will set RFIDTagReader.globalTag
        tagReader =RFIDTagReader.TagReader (task.serialPort, doChecksum = True, timeOutSecs = 0.05, kind='ID')
        tagReader.installCallBack (task.TIRpin)
        setattr(task, 'tagReader', tagReader)
        
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
