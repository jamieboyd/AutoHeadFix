#! /usr/bin/python3
#-*-coding: utf-8 -*-

# local files, part of AutoHeadFix
from AHF_Settings import AHF_Settings
from AHF_CageSet import AHF_CageSet
from AHF_Rewarder import AHF_Rewarder
from AHF_Camera import AHF_Camera
from RFIDTagReader import RFIDTagReader
from AHF_Notifier import AHF_Notifier
from AHF_UDPTrig import AHF_UDPTrig
from AHF_Stimulator import AHF_Stimulator
from AHF_HardwareTester import hardwareTester
from AHF_ValveControl import valveControl
from AHF_Mouse import Mouse, Mice
from AHF_HeadFixer import AHF_HeadFixer
from AHF_LickDetector import AHF_LickDetector, Simple_Logger
# Python modules - should all be present in default distribution
from os import path
from os import makedirs
from os import chown
from pwd import getpwnam
from grp import getgrnam
from time import time, localtime,timezone, sleep
from datetime import datetime, timedelta
from random import random
from sys import argv
#library import - need to have RPi.GPIO installed, but should be standard on Raspbian Woody or Jessie
import RPi.GPIO as GPIO

# constants used for calculating when to start a new day
# we put each day's movies and text files in a separate folder, and keep separate stats
KSECSPERDAY = 86400
KSECSPERHOUR = 3600
KDAYSTARTHOUR =7 # when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM

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
        # Create folders where the files for today will be stored
        makeDayFolderPath(expSettings, cageSettings)
        # initialize mice with zero mice
        mice = Mice()
        # make daily Log files and quick stats file
        makeLogFile (expSettings, cageSettings)
        makeQuickStatsFile (expSettings, cageSettings, mice)
        # set up the GPIO pins for each for their respective functionalities.
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup (cageSettings.ledPin, GPIO.OUT, initial = GPIO.LOW) # turns on brain illumination LED
        GPIO.setup (cageSettings.tirPin, GPIO.IN)  # Tag-in-range output from RFID tatg reader
        GPIO.setup (cageSettings.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + cageSettings.contactPUD))
        if cageSettings.contactPolarity == 'RISING':
            expSettings.contactEdge = GPIO.RISING 
            expSettings.noContactEdge = GPIO.FALLING
            expSettings.contactState = GPIO.HIGH
            expSettings.noContactState = GPIO.LOW
        else:
            expSettings.contactEdge = GPIO.FALLING
            expSettings.noContactEdge = GPIO.RISING 
            expSettings.contactState = GPIO.LOW
            expSettings.noContactState = GPIO.HIGH
        # make head fixer - does its own GPIO initialization from info in cageSettings
        headFixer=AHF_HeadFixer.get_class (cageSettings.headFixer) (cageSettings)
        # make a rewarder
        rewarder = AHF_Rewarder (30e-03, cageSettings.rewardPin)
        rewarder.addToDict('entrance', expSettings.entranceRewardTime)
        rewarder.addToDict ('task', expSettings.taskRewardTime)
        # make a notifier object
        if expSettings.hasTextMsg == True:
            notifier = AHF_Notifier (cageSettings.cageID, expSettings.phoneList)
        else:
            notifier = None
        # make RFID reader
        tagReader = RFIDTagReader(cageSettings.serialPort, False)
        # configure camera
        camera = AHF_Camera(expSettings.camParamsDict)
        # make UDP Trigger
        if expSettings.hasUDP == True:
            UDPTrigger = AHF_UDPTrig (expSettings.UDPList)
            print (UDPTrigger)
        else:
            UDPTrigger = None
        # make a lick detector
        simpleLogger = Simple_Logger (expSettings.logFP)
        lickDetector = AHF_LickDetector ((0,1),21,simpleLogger)
        lickDetector.start_logging ()
        # make stimulator
        stimulator = AHF_Stimulator.get_class (expSettings.stimulator)(expSettings.stimDict, rewarder, lickDetector, expSettings.logFP)
        expSettings.stimDict = stimulator.configDict
    except Exception as anError:
        print ('Unexpected error starting AutoHeadFix:', str (anError))
        raise anError
        return
    try:
        print ('Waiting for a mouse...')
        while True: #start main loop
            try:
                # wait for mouse entry, with occasional timeout to catch keyboard interrupt
                GPIO.wait_for_edge (cageSettings.tirPin, GPIO.RISING, timeout= kTIMEOUTmS) # wait for entry based on Tag-in-range pin
                if (GPIO.input (cageSettings.tirPin) == GPIO.HIGH):
                    try:
                        tag = tagReader.readTag ()
                    except (IOError, ValueError):
                        tagReader.clearBuffer()
                        continue
                    entryTime = time()
                    thisMouse = mice.getMouseFromTag (tag)
                    if thisMouse is None:
                        # try to open mouse config file to initialize mouse data
                        thisMouse=Mouse(tag,1,0,0,0)
                        mice.addMouse (thisMouse, expSettings.statsFP)
                    writeToLogFile(expSettings.logFP, thisMouse, 'entry')
                    thisMouse.entries += 1
                    # if we have entrance reward, first wait for entrance reward or first head-fix, which countermands entry reward
                    if thisMouse.entranceRewards < expSettings.maxEntryRewards:
                        giveEntranceReward = True
                        expSettings.doHeadFix = expSettings.propHeadFix > random()
                        while GPIO.input (cageSettings.tirPin)== GPIO.HIGH and time() < (entryTime + expSettings.entryRewardDelay):
                            GPIO.wait_for_edge (cageSettings.contactPin, expSettings.contactEdge, timeout= kTIMEOUTmS)
                            if (GPIO.input (cageSettings.contactPin)== expSettings.contactState):
                                runTrial (thisMouse, expSettings, cageSettings, camera, rewarder, headFixer,stimulator, UDPTrigger)
                                giveEntranceReward = False
                                break
                        if (GPIO.input (cageSettings.tirPin)== GPIO.HIGH) and giveEntranceReward == True:
                            thisMouse.reward (rewarder, 'entrance') # entrance reward was not countermanded by an early headfix
                            thisMouse.entranceRewards += 1
                            writeToLogFile(expSettings.logFP, thisMouse, 'entryReward')
                    # wait for contacts and run trials till mouse exits or time in chamber exceeded
                    expSettings.doHeadFix = expSettings.propHeadFix > random()
                    while GPIO.input (cageSettings.tirPin)== GPIO.HIGH and time () < entryTime + expSettings.inChamberTimeLimit:
                        if (GPIO.input (cageSettings.contactPin)== expSettings.noContactState):
                            GPIO.wait_for_edge (cageSettings.contactPin, expSettings.contactEdge, timeout= kTIMEOUTmS)
                        if (GPIO.input (cageSettings.contactPin)== expSettings.contactState):
                            runTrial (thisMouse, expSettings, cageSettings, camera, rewarder, headFixer, stimulator, UDPTrigger)
                            expSettings.doHeadFix = expSettings.propHeadFix > random() # set doHeadFix for next contact
                    # either mouse left the chamber or has been in chamber too long
                    if GPIO.input (cageSettings.tirPin)== GPIO.HIGH and time () > entryTime + expSettings.inChamberTimeLimit:
                        # explictly turn off pistons, though they should be off at end of trial
                        headFixer.releaseMouse()
                        if expSettings.hasTextMsg == True:
                            notifier.notify (thisMouse.tag, (time() - entryTime),  True)
                        # wait for mouse to leave chamber, with no timeout, unless it left while we did last 3 lines
                        if GPIO.input (cageSettings.tirPin)== GPIO.HIGH:
                            GPIO.wait_for_edge (cageSettings.tirPin, GPIO.FALLING)
                        if expSettings.hasTextMsg == True:
                            notifier.notify (thisMouse.tag, (time() - entryTime), False)
                    tagReader.clearBuffer ()
                    # after exit, update stats
                    writeToLogFile(expSettings.logFP, thisMouse, 'exit')
                    updateStats (expSettings.statsFP, mice, thisMouse)
                    # after each exit check for a new day
                    if datetime.fromtimestamp (int (time())) > nextDay:
                        now = datetime.fromtimestamp (int (time()))
                        startTime = datetime (now.year, now.month, now.day, KDAYSTARTHOUR,0,0)
                        nextDay = startTime + timedelta (hours=24)
                        lickDetector.stop_logging ()
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
                        lickDetector.start_logging ()
                    print ('Waiting for a mouse...')
            except KeyboardInterrupt:
                GPIO.output(cageSettings.ledPin, GPIO.LOW)
                headFixer.releaseMouse()
                GPIO.output(cageSettings.rewardPin, GPIO.LOW)
                lickDetector.stop_logging ()
                while True:
                    event = input ('Enter:\nr to return to head fix trials\nq to quit\nv to run valve control\nh for hardware tester\nc for camera configuration\ne for experiment configuration\n:')
                    if event == 'r' or event == "R":
                        lickDetector.start_logging ()
                        break
                    elif event == 'q' or event == 'Q':
                        return
                    elif event == 'v' or event== "V":
                        valveControl (cageSettings)
                    elif event == 'h' or event == 'H':
                        hardwareTester(cageSettings, tagReader, headFixer)
                        if cageSettings.contactPolarity == 'RISING':
                            expSettings.contactEdge = GPIO.RISING 
                            expSettings.noContactEdge = GPIO.FALLING
                            expSettings.contactState = GPIO.HIGH
                            expSettings.noContactState = GPIO.LOW
                        else:
                            expSettings.contactEdge = GPIO.FALLING
                            expSettings.noContactEdge = GPIO.RISING 
                            expSettings.contactState = GPIO.LOW
                            expSettings.noContactState = GPIO.HIGH
                    elif event == 'c' or event == 'C':
                        camParams = camera.adjust_config_from_user ()
                    elif event == 'e' or event == 'E':
                        modCode = expSettings.edit_from_user ()
                        if modCode & 2:
                            stimulator = AHF_Stimulator.get_class (expSettings.stimulator)(expSettings.stimDict, rewarder, lickDetector, expSettings.logFP)
                        if modCode & 1:
                            stimulator.change_config (expSettings.stimDict)
            except IOError as e:
                print(e)
                print("Looks like we had trouble reading the tag.")
    except Exception as anError:
        print ('AutoHeadFix error:' + str (anError))
        raise anError
    finally:
        stimulator.quitting()
        GPIO.output(cageSettings.ledPin, False)
        headFixer.releaseMouse()
        GPIO.output(cageSettings.rewardPin, False)
        GPIO.cleanup()
        writeToLogFile(expSettings.logFP, None, 'SeshEnd')
        expSettings.logFP.close()
        expSettings.statsFP.close()
        print ('AutoHeadFix Stopped')

def runTrial (thisMouse, expSettings, cageSettings, camera, rewarder, headFixer, stimulator, UDPTrigger=None):
    """
    Runs a single AutoHeadFix trial, from the mouse making initial contact with the plate

    Controls turning on and off the blue brain illumination LED, starting and stopping the movie, and running the stimulus
    which includes giving rewards
        :param thisMouse: the mouse object representing nouse that is being head-fixed
        :param expSettings: experiment-specific settings, everything you need to know is stored in this object
        :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
        :param camera: The AHF_Camera object used to record video
        :param rewarder :object of AHF_Rewarder class that runs solenoid to give water rewards
        :param stimulator: object of a subclass of  AHF_Stimulator, which runs experiment, incuding giving rewards
        :param UDPTrigger: used if sending UDP signals to other Pi for behavioural observation
    """
    try:
        if expSettings.doHeadFix == True:
            headFixer.fixMouse()
            sleep(0.4) # wait a bit for things to settle, then re-check contacts
            if GPIO.input(cageSettings.contactPin) == expSettings.noContactState:
                # release mouse if no contact... :(
                headFixer.releaseMouse()
                writeToLogFile(expSettings.logFP, thisMouse, 'check-')
                return False
        #  non-head fix trial or check was successful
        if expSettings.doHeadFix == True:
            thisMouse.headFixes += 1
            writeToLogFile (expSettings.logFP, thisMouse, 'check+')
        else:
            writeToLogFile (expSettings.logFP, thisMouse,'check No Fix Trial')
        # Configure the stimulator and the path for the video
        stimStr = stimulator.configStim (thisMouse)
        headFixTime = time()
        
        #TODO IMPROVE
        if camera.AHFvideoFormat == 'rgb':
            extension = 'raw'
        else:
            extension = 'h264'

        video_name = str (thisMouse.tag) + "_" + stimStr + "_" + '%d' % headFixTime + '.' + extension
        video_name_path = expSettings.dayFolderPath + 'Videos/' + "M" + video_name
        writeToLogFile (expSettings.logFP, thisMouse, "video:" + video_name)
        # send socket message to start behavioural camera
        if expSettings.hasUDP == True:
            #MESSAGE = str (thisMouse.tag) + "_" + stimStr + "_" + '%d' % headFixTime
            MESSAGE = str (thisMouse.tag) + "_" +  "_" + '%d' % headFixTime
            UDPTrigger.doTrigger (MESSAGE)
            # start recording and Turn on the blue led
            camera.start_recording(video_name_path)
            sleep(expSettings.cameraStartDelay) # wait a bit so camera has time to start before light turns on, for synchrony accross cameras
            GPIO.output(cageSettings.ledPin, GPIO.HIGH)
            writeToLogFile (expSettings.logFP, thisMouse, "BrainLEDON")
        else: # turn on the blue light and start the movie
            GPIO.output(cageSettings.ledPin, GPIO.HIGH)
            camera.start_recording(video_name_path)
        stimulator.run () # run whatever stimulus is configured
        if expSettings.hasUDP == True:
            GPIO.output(cageSettings.ledPin, GPIO.LOW) # turn off the blue LED
            writeToLogFile (expSettings.logFP, thisMouse, "BrainLEDOFF")
            sleep(expSettings.cameraStartDelay) #wait again after turning off LED before stopping camera, for synchronization
            UDPTrigger.doTrigger ("Stop") # stop
            camera.stop_recording()
        else:
            camera.stop_recording()
            GPIO.output(cageSettings.ledPin, GPIO.LOW) # turn off the blue LED
        uid = getpwnam ('pi').pw_uid
        gid = getgrnam ('pi').gr_gid
        chown (video_name_path, uid, gid) # we run AutoheadFix as root if using pi PWM, so we expicitly set ownership to pi
        # skeddadleTime gives mouse a chance to disconnect before head fixing again
        skeddadleEnd = time() + expSettings.skeddadleTime
        if expSettings.doHeadFix == True:
            headFixer.releaseMouse()
            sleep (0.5) # need to be mindful that servo motors generate RF, so wait 
        stimulator.logfile ()
        writeToLogFile (expSettings.logFP, thisMouse,'complete')
        if (GPIO.input (cageSettings.contactPin)== expSettings.contactState):
            while time () < skeddadleEnd:
                GPIO.wait_for_edge (cageSettings.contactPin, expSettings.noContactEdge, timeout= kTIMEOUTmS)
                if (GPIO.input (cageSettings.contactPin)== expSettings.noContactState):
                    break
        return True
    except Exception as anError:
        headFixer.releaseMouse()
        camera.stop_recording()
        print ('Error in running trial:' + str (anError))
        raise anError


def makeDayFolderPath (expSettings, cageSettings):
    """
    Makes data folders for a day's data,including movies, log file, and quick stats file

    Format: dayFolder = cageSettings.dataPath + cageSettings.cageID + YYYMMMDD
    within which will be /Videos and /TextFiles
    :param expSettings: experiment-specific settings, everything you need to know is stored in this object
    :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO

    """
    dateTimeStruct = localtime()
    expSettings.dateStr= str (dateTimeStruct.tm_year) + (str (dateTimeStruct.tm_mon)).zfill(2) + (str (dateTimeStruct.tm_mday)).zfill(2)
    expSettings.dayFolderPath = cageSettings.dataPath + expSettings.dateStr + '/' + cageSettings.cageID + '/'
    if not path.exists(expSettings.dayFolderPath):
        makedirs(expSettings.dayFolderPath, mode=0o777, exist_ok=True)
        makedirs(expSettings.dayFolderPath + 'TextFiles/', mode=0o777, exist_ok=True)
        makedirs(expSettings.dayFolderPath + 'Videos/', mode=0o777, exist_ok=True)
        uid = getpwnam ('pi').pw_uid
        gid = getgrnam ('pi').gr_gid
        chown (expSettings.dayFolderPath, uid, gid)
        chown (expSettings.dayFolderPath + 'TextFiles/', uid, gid)
        chown (expSettings.dayFolderPath + 'Videos/', uid, gid)
        

def makeLogFile (expSettings, cageSettings):
    """
    open a new text log file for today, or open an exisiting text file with 'a' for append
    """
    logFilePath = expSettings.dayFolderPath + 'TextFiles/headFix_' + cageSettings.cageID + '_' + expSettings.dateStr + '.txt'
    expSettings.logFP = open(logFilePath, 'a')
    uid = getpwnam ('pi').pw_uid
    gid = getgrnam ('pi').gr_gid
    chown (logFilePath, uid, gid)
    writeToLogFile (expSettings.logFP, None, 'SeshStart')

def writeToLogFile(logFP, mouseObj, event):
    """
    Writes the time and type of each event to a text log file, and also to the shell

    Format of the output string: tag     time_epoch or datetime       event
    The computer-parsable time_epoch is printed to the log file and user-friendly datetime is printed to the shell
    :param logFP: file pointer to the log file
    :param mouseObj: the mouse for which the event pertains, 
    :param event: the type of event to be printed, entry, exit, reward, etc.
    returns: nothing
    """
    if event == 'SeshStart' or event == 'SeshEnd' or mouseObj is None:
        outPutStr = ''.zfill(13)
    else:
        outPutStr = '{:013}'.format(mouseObj.tag)
    logOutPutStr = outPutStr + '\t' + '{:.2f}'.format (time ())  + '\t' + event +  '\t' + datetime.fromtimestamp (int (time())).isoformat (' ')
    printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
    print (printOutPutStr)
    logFP.write(logOutPutStr + '\n')
    logFP.flush()


def makeQuickStatsFile (expSettings, cageSettings, mice):
    """
    makes a new quickStats file for today, or opens an existing file to append.
    
    QuickStats file contains daily totals of rewards and headFixes for each mouse
    :param expSettings: experiment-specific settings, everything you need to know is stored in this object
    :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
    :param mice: the array of mice objects for this cage
"""
    textFilePath = expSettings.dayFolderPath + 'TextFiles/quickStats_' + cageSettings.cageID + '_' + expSettings.dateStr + '.txt'
    if path.exists(textFilePath):
        expSettings.statsFP = open(textFilePath, 'r+')
        mice.addMiceFromFile(expSettings.statsFP)
        mice.show()
    else:
        expSettings.statsFP = open(textFilePath, 'w')
        expSettings.statsFP.write('Mouse_ID\tentries\tent_rew\thfixes\thf_rew\n')
        expSettings.statsFP.close()
        expSettings.statsFP = open(textFilePath, 'r+')
        uid = getpwnam ('pi').pw_uid
        gid = getgrnam ('pi').gr_gid
        chown (textFilePath, uid, gid)


def updateStats (statsFP, mice, mouse):
    """ Updates the quick stats text file after every exit, mostly for the benefit of folks logged in remotely
    :param statsFP: file pointer to the stats file
    :param mice: the array of mouse objects
    :param mouse: the mouse which just left the chamber 
    returns:nothing
    """
    pos = mouse.arrayPos
    statsFP.seek (39 + 38 * pos) # calculate this mouse pos, skipping the 39 char header
    # we are in the right place in the file and new and existing values are zero-padded to the same length, so overwriting should work
    outPutStr = '{:013}'.format(mouse.tag) + "\t" +  '{:05}'.format(mouse.entries)
    outPutStr += "\t" +  '{:05}'.format(mouse.entranceRewards) + "\t" + '{:05}'.format(mouse.headFixes)
    outPutStr +=  "\t" + '{:05}'.format(mouse.headFixRewards) + "\n"
    statsFP.write (outPutStr)
    statsFP.flush()
    statsFP.seek (39 + 38 * mice.nMice()) # leave file position at end of file so when we quit, nothing is truncated


if __name__ == '__main__':
   main()
