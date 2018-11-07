#! /usr/bin/python3
#-*-coding: utf-8 -*-

#library imports
import RPi.GPIO as GPIO
from PTSimpleGPIO import PTSimpleGPIO, Pulse
from PTCountermandPulse import CountermandPulse


from RFIDTagReader import RFIDTagReader

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

"""
RFID reader object and tag need to be global so we can access them
easily from Tag-In-Range calback
"""
tagReader=None
tag =0
"""
Threaded call back function on Tag-In-Range pin
Updates tag global variable whenever Tag-In-Range pin toggles
Setting tag to 0 means no tag is presently in range
"""
def tagReaderCallback (channel):
    global tag # the global indicates that it is the same variable declared above and also used by main loop
    global tagReader
    if GPIO.input (channel) == GPIO.HIGH: # tag just entered
        try:
            tag = tagReader.readTag ()
        except Exception as e:
            tag = 0
    else:  # tag just left
        tag = 0

        

def main():
    """
    The main function for the AutoHeadFix program.

    It initializes or loads settings and configurations, then endlessly loops running entries and head fix trials
    Ctrl-C is used to enter a menu-driven mode where settings can be altered.
    """
    try:
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        configFile = None
#        if argv.__len__() > 1:
#            configFile = argv [1]
        task = Task (configFile) 
        print ('LED pin =', task.ledPin)
        """
        Initialize tag reader - the global keyword indicates these are the same variables
        used in the tagReader callback
        """
        global tag
        global tagReader
        tagReader = RFIDTagReader(task.serialPort, doCheckSum = True)
        GPIO.setup (task.tirPin, GPIO.IN)
        GPIO.add_event_detect (task.tirPin, GPIO.BOTH)
        GPIO.add_event_callback (task.tirPin, tagReaderCallback)
    except Exception as e:
        print ('error starting AutoHeadFix:' + str (e))
        raise e
    # do some GPIO setup
    GPIO.setmode (GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup (task.ledPin, GPIO.OUT, initial = GPIO.LOW) # turns on brain illumination LED
    GPIO.setup (task.tirPin, GPIO.IN)  # Tag-in-range output from RFID tatg reader
    GPIO.setup (task.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + task.contactPUD))
    # make head fixer - does its own GPIO initialization from info in cageSettings
    headFixer=AHF_HeadFixer.get_class(task.headFixerName)(task)
    # make rewarder - uses PTSimpleGPIO
    rewarder = CountermandPulse (task.rewardPin, 0, 0.01, 0.01, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
    # make a notifier object
    if expSettings.hasTextMsg == True:
        from AHF_Notifier import AHF_Notifier
        notifier = AHF_Notifier (task.cageID, task.phoneList)
    else:
        notifier = None

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
