#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base
from AHF_Mouse import Mice, Mouse

class AHF_Stimulator (AHF_Base, metaclass = ABCMeta):

    """
    Stimulator does all stimulation and reward during a head fix task
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.

    """


    @abstractmethod
    def run (self, resultsDict = {}, settingsDict = {}):
        """
        Called at start of each head fix. Does whatever
        """
        pass




    def startCamera (self):

        # TODO: Save images within HDF5 code for each event
        # Save with file name and timestamp, the rest of the information
        # should be in the text file
        # End goal: Use database with text file, then use result of database
        # to find images in HDF5.

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
        video_name_path = '/home/pi/Documents/' + "M" + video_name
        #writeToLogFile (expSettings.logFP, thisMouse, "video:" + video_name)
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
