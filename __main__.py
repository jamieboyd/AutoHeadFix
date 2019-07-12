#! /usr/bin/python3
#-*-coding: utf-8 -*-

# local files, part of AutoHeadFix
from AHF_CageSet import AHF_CageSet
from AHF_Settings import AHF_Settings
from AHF_Rewarder import AHF_Rewarder
from AHF_HeadFixer import AHF_HeadFixer
from AHF_Camera import AHF_Camera
import RFIDTagReader
from AHF_Stimulator import AHF_Stimulator
from AHF_HardwareTester import hardwareTester  
from AHF_Mouse import Mouse, Mice

#Standard Python modules
from os import path, makedirs, listdir, chown
from pwd import getpwnam
from grp import getgrnam
from time import time, sleep
from datetime import datetime, timedelta
from random import random
from sys import argv, exit
# raspberry Pi specific module, RPi
import RPi.GPIO as GPIO

"""
constant used for calculating when to start a new day
we put each day's movies and text files in a separate folder, and keep separate stats
"""
KDAYSTARTHOUR =13 # when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM

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
        """
        load general settings for this cage, mostly hardware pinouts, things not expected to change often 
        there is only one AHFconfig.jsn file, in the enclosing folder
        """
        cageSettings = AHF_CageSet()
        """""
        get settings that may vary by experiment, including rewarder, camera parameters, and stimulator
        More than one of these files can exist, and the user needs to choose one or make one
        we will add some other variables to expSettings so we can pass them as a single argument to functions
        logFP, statsFP, dateStr, dayFolderPath, doHeadFix, 
        expSettings File can be specified if launched from command line, eg, sudo python3 myconfig or sudo python3 AHF_Settings_myconfig.jsn
        """
        if argv.__len__() > 1:
            expSettings = AHF_Settings (argv [1])
        else:
            expSettings = AHF_Settings ()
        # nextDay starts tomorrow at KDAYSTARTHOUR
        now = datetime.fromtimestamp (time())
        startTime = datetime (now.year, now.month,now.day, KDAYSTARTHOUR,0,0)
        nextDay = startTime + timedelta (hours=24)
        # Create folders where the files for today will be stored
        makeDayFolderPath(expSettings, cageSettings)
        # make daily Log file and quickStats file - at this point mice not initialized
        makeLogFile (expSettings, cageSettings)
        makeQuickStatsFile (expSettings, cageSettings)
        # initialize mice, with mice from today's quickStats, if it exists, else with zero mice and we add them as we see them
        mice = Mice(expSettings.statsFP)
        # set up the GPIO pins for each for their respective functionalities.
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings (False)
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
        # make a rewarder, a simple class with no sub-classing, opens a solenoid valve
        rewarder = AHF_Rewarder (30e-03, cageSettings.rewardPin)
        rewarder.addToDict('entrance', expSettings.entranceRewardTime)
        rewarder.addToDict ('task', expSettings.taskRewardTime)
        # make a notifier object, if requested in settings
        if expSettings.hasTextMsg:
            from AHF_Notifier import AHF_Notifier
            notifier = AHF_Notifier (cageSettings.cageID, expSettings.phoneList)
        else:
            notifier = None
        # make RFID reader and install callback
        tagReader = RFIDTagReader.TagReader(cageSettings.serialPort, True, timeOutSecs = kTIMEOUTSECS)
        tagReader.installCallback (cageSettings.tirPin)
        # configure camera
        camera = AHF_Camera(expSettings.camParamsDict)
        # make UDP Trigger
        if expSettings.hasUDP:
            from AHF_UDPTrig import AHF_UDPTrig
            UDPTrigger = AHF_UDPTrig (expSettings.UDPList)
        else:
            UDPTrigger = None
        # make a lick detector
        if cageSettings.lickIRQ == 0:
            lickDetector = None
        else:
            from AHF_LickDetector import AHF_LickDetector
            lickDetector = AHF_LickDetector (cageSettings.lickChans, cageSettings.lickIRQ, expSettings.logFP)
            lickDetector.start_logging ()
        # make stimulator, passing it cageSettings, expSettings, rewarder, and lickDetector. It needs to be made last
        stimulator = AHF_Stimulator.get_class (expSettings.stimulator)(cageSettings, expSettings, rewarder, lickDetector)
    except Exception as anError:
        print ('Unexpected error starting AutoHeadFix:{}'.format(anError))
        raise anError
        exit(0)
    try:
        while True: # looping over entries, exits
            try:
                print ('Waiting for a mouse...')
                while RFIDTagReader.globalTag == 0:
                    if datetime.fromtimestamp (time()) > nextDay:
                        now = datetime.fromtimestamp (time())
                        startTime = datetime (now.year, now.month, now.day, KDAYSTARTHOUR,0,0)
                        nextDay = startTime + timedelta (hours=24)
                        if lickDetector is not None:
                            lickDetector.stop_logging ()
                        mice.show()
                        stimulator.nextDay (expSettings.statsFP, mice)
                        mice.clear ()
                        writeToLogFile(expSettings.logFP, None, 'SeshEnd')
                        expSettings.logFP.close()
                        expSettings.statsFP.close()
                        makeDayFolderPath(expSettings, cageSettings)
                        makeLogFile (expSettings, cageSettings)
                        makeQuickStatsFile (expSettings, cageSettings, mice)
                        if lickDetector is not None:
                            lickDetector.dataLogger.logFP = expSettings.logFP
                            lickDetector.touched()
                            lickDetector.start_logging()
                    else:
                        sleep (kTIMEOUTSECS)
                # a mouse has entered
                tag = RFIDTagReader.globalTag
                entryTime = time()
                thisMouse = mice.getMouseFromTag (tag)
                if thisMouse is None:
                    thisMouse=Mouse(tag,1,0,0, {})
                    mice.addMouse (thisMouse, expSettings.statsFP)
                writeToLogFile(expSettings.logFP, thisMouse, 'entry')
                thisMouse.entries += 1
                # if we have entrance reward, give countermandable entry reward - early exit countermands reward
                if thisMouse.entranceRewards < expSettings.maxEntryRewards:
                   rewarder.giveRewardCM ('entry', expSettings.entryRewardDelay)
                # loop through contacts/running trials till mouse exits or time in chamber exceeded
                while RFIDTagReader.globalTag == tag and time () < entryTime + expSettings.inChamberTimeLimit:
                    if GPIO.input (cageSettings.contactPin) == expSettings.noContactState:
                        if GPIO.wait_for_edge (cageSettings.contactPin, expSettings.contactEdge, timeout= int (kTIMEOUTSECS * 1000)) == None:
                            sleep (kTIMEOUTSECS)
                    else:
                        # ready to head fix
                        expSettings.doHeadFix = expSettings.propHeadFix > random()
                        if expSettings.doHeadFix == True:
                            headFixer.fixMouse()
                            sleep(0.4) # wait a bit for things to settle, then re-check contacts
                            if GPIO.input(cageSettings.contactPin) == expSettings.noContactState:
                                # release mouse if no contact... :(
                                headFixer.releaseMouse()
                                writeToLogFile (expSettings.logFP, thisMouse, 'check-')
                                continue
                        #  non-head fix trial or check was successful
                        headFixTime = time()
                        if expSettings.doHeadFix == True:
                            thisMouse.headFixes += 1
                            writeToLogFile (expSettings.logFP, thisMouse, 'check+')
                        else:
                            writeToLogFile (expSettings.logFP, thisMouse,'check No Fix Trial')
                        # Configure the stimulator to get the path for the video
                        stimStr = stimulator.configStim (thisMouse)
                        # analysis code expects brain data, in rgb format, to have .raw extension. 
                        if camera.AHFvideoFormat == 'rgb':
                            extension = 'raw'
                        video_name = str (thisMouse.tag) + "_" + stimStr + "_" + '%d' % headFixTime + '.' + extension
                        video_name_path = expSettings.dayFolderPath + 'Videos/' + "M" + video_name
                        writeToLogFile (expSettings.logFP, thisMouse, "video:" + video_name)
                        # send socket message to start behavioural cameras
                        if expSettings.hasUDP == True:
                            MESSAGE = '{:d}_{:s}_{:d}'.format (thisMouse.tag, stimStr, int (headFixTime))
                            UDPTrigger.doTrigger (MESSAGE)
                            # start recording and Turn on the blue led
                            camera.start_recording(video_name_path)
                            sleep(expSettings.cameraStartDelay) # wait a bit so camera has time to start before light turns on, for synchrony accross cameras
                            GPIO.output(cageSettings.ledPin, GPIO.HIGH)
                            writeToLogFile (expSettings.logFP, thisMouse, "BrainLEDON")
                        else: # turn on the blue light and start the movie right away
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
                        stimulator.logfile ()
                        writeToLogFile (expSettings.logFP, thisMouse,'complete')
                        if expSettings.doHeadFix == True:
                            headFixer.releaseMouse()
                            # skeddadleTime gives mouse a chance to disconnect before head fixing again
                            skeddadleEnd = time() + expSettings.skeddadleTime
                            #sleep (0.5) # need to be mindful that servo motors generate RF, so wait 
                            if (GPIO.input (cageSettings.contactPin)== expSettings.contactState):
                                while time () < skeddadleEnd:
                                    if GPIO.wait_for_edge (cageSettings.contactPin, expSettings.noContactEdge, timeout= int (kTIMEOUTSECS * 1000)) == None:
                                        sleep (kTIMEOUTSECS)
                                    else:
                                        break
                # either mouse left the chamber or has been in chamber too long
                if time () > entryTime + expSettings.inChamberTimeLimit:
                    # explictly turn off headfixer, though it should be off at end of trial
                    headFixer.releaseMouse()
                    if expSettings.hasTextMsg == True:
                        notifier.notify (thisMouse.tag, (time() - entryTime),  True)
                    # wait for mouse to leave chamber
                    while RFIDTagReader.globalTag == tag:
                        sleep (kTIMEOUTSECS)
                    if expSettings.hasTextMsg == True:
                        notifier.notify (thisMouse.tag, (time() - entryTime), False)
                # after exit, look to countermand entrance reward and update stats
                if thisMouse.entranceRewards < expSettings.maxEntryRewards:
                   if not rewarder.countermandReward ():
                       thisMouse.entranceRewards +=1
                writeToLogFile(expSettings.logFP, thisMouse, 'exit')
                thisMouse.updateStats (expSettings.statsFP)
            except KeyboardInterrupt:
                GPIO.output(cageSettings.ledPin, GPIO.LOW)
                headFixer.releaseMouse()
                if lickDetector is not None:
                    lickDetector.stop_logging ()
                while True:
                    event = input ('Enter:\nr to return to head fix trials\nq to quit\nv to run valve control\nh for hardware tester\nc for camera configuration\ne for experiment configuration\n:')
                    if event == 'r' or event == "R": # return to running trials
                        if lickDetector is not None:
                            lickDetector.touched()
                            lickDetector.start_logging ()
                        break
                    elif event == 'q' or event == 'Q': # exit program
                        exit(0)
                    elif event == 'v' or event== "V": # open and close valve
                        rewarder.valveControl()
                    elif event == 'h' or event == 'H': # run hardware tester to test hardware and stimulator
                        hardwareTester(cageSettings, expSettings, tagReader, headFixer, rewarder, lickDetector, stimulator)
                    elif event == 'c' or event == 'C':
                        camParams = camera.adjust_config_from_user () # adjust camera settings
                    elif event == 'e' or event == 'E':      # adjust experiment settings, including stimulator and dictionary
                        modCode = expSettings.edit_from_user ()
                        if modCode & 2: # we need to remake the stimulator
                            stimulator = AHF_Stimulator.get_class (expSettings.stimulator)(cageSettings, expSettings, rewarder, lickDetector)
                        if modCode & 1: # we need to redo setup after changing dictionary
                            stimulator.configDict = expSettings.stimDict
                            stimulator.setup ()
    except Exception as anError:
        print ('AutoHeadFix error:' + str (anError))
        raise anError
    finally:
        stimulator.quitting()
        GPIO.output(cageSettings.ledPin, False)
        headFixer.releaseMouse()
        GPIO.cleanup()
        writeToLogFile(expSettings.logFP, None, 'SeshEnd')
        expSettings.logFP.close()
        expSettings.statsFP.close()
        print ('AutoHeadFix Stopped')

def runTrial (thisMouse, expSettings, cageSettings, camera, rewarder, headFixer, stimulator, UDPTrigger):
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
        # Configure the stimulator to get the path for the video
        stimStr = stimulator.configStim (thisMouse)
        headFixTime = time()
        # analysis code expects brain data, in rgb format, to have .raw extension
        if camera.AHFvideoFormat == 'rgb':
            extension = 'raw'
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
                GPIO.wait_for_edge (cageSettings.contactPin, expSettings.noContactEdge, timeout= int(kTIMEOUTS * 1000))
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
    :param cageSettings: settings that are expected to stay the same for a setup, including cageID

    """
    now = datetime.fromtimestamp (time())
    expSettings.dateStr = '{:04d}{:02d}{:02d}'.format(now.year, now.month,now.day) 
    expSettings.dayFolderPath ='{:s}{:s}/{:s}/'.format(cageSettings.dataPath, expSettings.dateStr, cageSettings.cageID)
    try:
        if not path.exists(expSettings.dayFolderPath):
            makedirs(expSettings.dayFolderPath, mode=0o777, exist_ok=True)
            makedirs(expSettings.dayFolderPath + 'TextFiles/', mode=0o777, exist_ok=True)
            makedirs(expSettings.dayFolderPath + 'Videos/', mode=0o777, exist_ok=True)
            uid = getpwnam ('pi').pw_uid
            gid = getgrnam ('pi').gr_gid
            chown (expSettings.dayFolderPath, uid, gid)
            chown (expSettings.dayFolderPath + 'TextFiles/', uid, gid)
            chown (expSettings.dayFolderPath + 'Videos/', uid, gid)
    except Exception as e:
            print ("Error making directories\n", str(e))
        

def makeLogFile (expSettings, cageSettings):
    """
    open a new text log file for today, or opens an exisiting log file using 'a+' for append
    """
    try:
        logFilePath ='{:s}TextFiles/headFix_{:s}_{:s}.txt'.format(expSettings.dayFolderPath, cageSettings.cageID, expSettings.dateStr)
        expSettings.logFP = open(logFilePath, 'a+')
        uid = getpwnam ('pi').pw_uid
        gid = getgrnam ('pi').gr_gid
        chown (logFilePath, uid, gid)
        writeToLogFile (expSettings.logFP, None, 'SeshStart')
    except Exception as e:
            print ("Error maing log file\n", str(e))

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
    try:
        # get unix time for time stamp, and get human readable format
        now = time()
        humanTime = datetime.fromtimestamp (int (now)).isoformat (' ')
        if event == 'SeshStart' or event == 'SeshEnd' or mouseObj is None:
            mouseNum = 0
        else:
            mouseNum= mouseObj.tag
        # print  to file    mouse   unix_time   event   human_time
        logFP.write('{:013d}\t{:.2f}\t{:s}\t{:s}\n'.format (mouseNum, now, event, humanTime))
        # print to shell   mouse   human_time   event
        print ('{:013d}\t{:s}\t{:s}'.format (mouseNum, humanTime, event))
        logFP.flush()
    except Exception as e:
        print ("Error writing to log file\n", str (e))
        raise e

def makeQuickStatsFile (expSettings, cageSettings, mice = None):
    """
    makes a new quickStats file for today, or opens an existing file to append.
    QuickStats file contains daily totals of rewards and headFixes for each mouse
    :param expSettings: experiment-specific settings, everything you need to know is stored in this object
    :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
    :param mice: the array of mice objects for this cage, or None when program fist launches and no mice yet

    Stimulator can add results dictionary for each mouse
    """
    try:
        textFilePath ='{:s}TextFiles/quickStats_{:s}_{:s}.txt'.format(expSettings.dayFolderPath, cageSettings.cageID, expSettings.dateStr)
        if path.exists(textFilePath):
            expSettings.statsFP = open(textFilePath, 'r+') # if file exists, open for editing, not truncating or appending
        else:
            expSettings.statsFP = open(textFilePath, 'w+') # if file does not exist, open, write header, and set permissions
            expSettings.statsFP.write('Mouse_ID\tentries\tent_rew\thfixes\tstim_dict\n')
            uid = getpwnam ('pi').pw_uid
            gid = getgrnam ('pi').gr_gid
            chown (textFilePath, uid, gid)
    except Exception as e:
        print ('Error making quickStats file:{}', e)
        raise e
    # if we have mice, write the mice data to the file
    if mice is not None:
        for mouse in mice.generator():
            outPutStr = '{:013d}\t{:05d}\t{:05d}\t{:05d}\t{:s}\n'.format(mouse.tag, mouse.entries, mouse.entranceRewards, mouse.headFixes, json.dumps(mouse.stimResultsDict))
            statsFile.write (outPutStr)
        



if __name__ == '__main__':
   main()
