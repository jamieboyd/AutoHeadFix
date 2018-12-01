#! /usr/bin/python
#-*-coding: utf-8 -*-

from time import time, sleep
from datetime import datetime
import RPi.GPIO as GPIO
import Adafruit_MPR121.MPR121 as MPR121
from array import array

"""
Adafruit_MPR121 requires the Adafuit MPR121 library which, in turn,
requires the Adafuit GPIO library
git clone https://github.com/adafruit/Adafruit_Python_MPR121
git clone https://github.com/adafruit/Adafruit_Python_GPIO

imports Adafruit_GPIO for the i2c library. The file
/Adafruit_Python_GPIO/Adafruit_GPIO/Adafruit_GPIO/I2C.py contains a function,
require_repeated_start, that fails with newer OS verions. It tries to edit
a file, '/sys/module/i2c_bcm2708/parameters/combined', that may no longer exist.
Replace the file name with '/sys/module/i2c_bcm2835/parameters/debug' reinstall,
and try again.

        subprocess.check_call('chmod 666 /sys/module/i2c_bcm2835/parameters/debug', shell=True)
        subprocess.check_call('echo -n 1 > /sys/module/i2c_bcm2835/parameters/debug', shell=True)
"""

# Globals for interacting with lickDetector callback
gLickDetector = None        # will be initialized with MPR121 capacitive sensor object
gLickTouches = 0            # raw state of touch sensor
gLickArray = None           # array for counting licks in callback, will be initialized with 10 ints 


def AHF_LickDetectorCallback (channel):
    """
    Lick Detetctor Calback, updates global for touches, adds new touches to global array, possibly logs licks
    If callback is running, do not interact with mpr121 directly, only through globals set by callback function
    Callback tracks only touches, not un-touches, by keeping track of last touches
    mpr121.touched() returns a 12-but value  where each bit  represents a pin, with a value of 1 being touched
    and 0 being not touched.
    """
    global gLickDetector
    global gLickTouches
    global gLickArray
    gLickTouches = gLickDetector.mpr121.touched()
    # compare current touches to previous touchs to find new touches
    pinBit =1
    for i in range (0,10):
        if (gLickTouches & pinBit) and not (gLickDetector.prevTouches & pinBit):
            gLickArray [i] +=1
            if gLickDetector.isLogging:
                gLickDetector.dataLogger.writeToLogFile('Lick:' + str (i))
        pinBit *= 2
    gLickDetector.prevTouches = gLickTouches

    
class LickDetector (object):
    """
    Lick detector class runs the MPR121 capacitive touch sensor. Has 10 channels. Only used here in touched or not toched mode, not
    analog signals. Note the seting of touch and untouch thresholds. MPR121 IRQ pin is toggled whenever a touch or untouch is registered.
    Used to trigger AHF_LickDetectorCallback.
    """
    def __init__(self, IRQ_PIN, data_logger):
        # initialize capacitive sensor gobal object and start it up
        self.mpr121 = MPR121.MPR121()
        self.mpr121.begin()
        self.mpr121.set_thresholds (8,4) # touch and untouch thresholds as per dirkjan
        self.hasCallback = False
        self.IRQ_PIN =IRQ_PIN
        GPIO.setup(self.IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if data_logger is None:
            self.dataLogger = Simple_Logger (None)
        else:
            self.dataLogger= data_logger
        self.isLogging = False
        self.prevTouches =0
        global gLickDetector
        gLickDetector = self
        global gLickArray
        gLickArray = array ('i', [0]*10)

    def resetDetector (self):
        """
        Calls MPR121 reset function. Should rarely need to do this? This could be of use in resetting baseline untouched values.
        """
        self.mpr121._reset ()

    def startCallback (self):
        """
        starts the AHF_LickDetectorCallback function running
        """
        if self.hasCallback:
            return
        # set up IRQ interrupt function. GPIO.setmode should alreay have been called
        GPIO.setup(self.IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect (self.IRQ_PIN,  GPIO.FALLING)
        GPIO.add_event_callback (self.IRQ_PIN, AHF_LickDetectorCallback)        
        self.hasCallack = True
        # state of touches from one invocation to next, used in callback to separate touches from untouches
        self.prevTouches = self.mpr121.touched()


    def stopCallback (self):
        """
        stops AHF_LickDetectorCallback from running, but it can be restarted
        """
        GPIO.remove_event_detect (self.IRQ_PIN)
        self.hasCallback = False

    def startLogging (self):
        """
        tells the AHF_LickDetectorCallback to log touches in shell and file (if present)
        starts the callback running, if not alreasdy running
        """
        self.isLogging = True
        self.startCallback ()

    def stopLogging (self):
        """
        tells the AHF_LickDetectorCallback to stop logging touches in shell and file (if present)
        """
        self.isLogging = False
 

    def getTouches (self):
        """
        If callback is running, returns value of global for touches, else gets touches from mpr121
        """
        if self.hasCallback:
            global gLickTouches
            return gLickTouches
        else:
            return self.mpr121.touched ()


    def waitForLick (self, timeOut_secs, startFromZero=False):
        """
        Waits for a lick on any channel. Returns channel that was touched, or 0 if timeout expires with no touch,
        or -1 if startFromZero was True and the detector was touched for entire time
        if the callback is installed, we monitor gLickTouches, else we use GPIO.wait_for_edge on the IRQ pin
        Note that if you call GPIO.wait_for_edge after calling add_event_detect for the same pin, you will have a bad time
        """
        if self.hasCallback:
            self.mpr121.touched()
            endTime = time() + timeOut_secs
            global gLickTouches
            touched = gLickTouches
            if touched == 0: # no touches now, wait for first touch, or timeout expiry
                while gLickTouches ==0 and time() < endTime:
                    sleep (0.05)
                return gLickTouches
            else: #touches already registered
                if not startFromZero: # we are done already
                    return touched
                else: # we first wait till there are no touches, or time has expired
                    while gLickTouches > 0 and time() < endTime:
                        sleep (0.05)
                    if time() > endTime: # touched till timeout expired
                        return -1
                    else: # now wait for touch or til timeout expires
                        while gLickTouches == 0 and time() < endTime:
                            sleep (0.05)
                        return gLickTouches # will be the channel touched, or 0 if no touches till timeout expires
        else:
            touched = self.mpr121.touched ()
            if touched == 0: # no touches now, wait for first touch, or timout expiry
                event = GPIO.wait_for_edge (self.IRQ_PIN, GPIO.FALLING, timeout = timeOut_secs * 1000)
                if event is not None:
                    return self.mpr121.touched ()
                else:
                    return 0
            else: # touches already registered
                if not startFromZero: # we are done already
                    return touched
                else: # we first wait till there are no touches, or time has expired
                    endTime = time() + timeOut_secs
                    while time() < endTime:
                        timeOutVal = int ((endTime - time()) * 1000)
                        event = GPIO.wait_for_edge (self.IRQ_PIN, GPIO.FALLING, timeout = timeOutVal)
                        if event is not None:
                            touched = self.mpr121.touched ()
                            if touched == 0:
                                break
                    if time () > endTime: # touched till timeout expired
                        self.mpr121.touched () # clears IRQ
                        return -1
                    else: # now wait for touch or till timeout expires
                        timeOutVal = (endTime - time()) * 1000
                        event = GPIO.wait_for_edge (self.IRQ_PIN, GPIO.FALLING, timeout = timeOutVal)
                        return self.mpr121.touched () # will be the channel touched, or 0 if no touches till timeout expires


    def zeroLickCount (self, chanList):
        """
        Zeros the selected list of channels in the global array of licks per channel that the callback function updates.
        Use it to count licks, by zeroing selected channels, then checking the values in the array
        """
        global gLickArray
        for chan in chanList:
            gLickArray [chan] = 0
            

    def getLickCount (self, chanList):
        """
        takes a list of channels and returns a list where each member is the number of licks for that channel in the global array
        """
        global gLickArray
        returnList = []
        for chan in chanList:
            returnList.append (gLickArray[chan])
        return returnList
        
 
    def test (self, cageSet):
        """
        tests the lick detector, designed to called by the hardware tester, can modify IRQ pin in hardware settings
        If asked to change IRQ pin, also resets the detector
        """
        self.startCallback()
        self.startLogging ()
        lickError = 0
        print ('\nLick detetctor waiting 10 seconds for a touch....')
        lick = self.waitForLick (10, True)
        self.stopCallback()
        if lick < 1:
            if lick == -1:
                inputStr= input('Touches were registered the whole 10 seconds. Do you want to change IRQ pin, currently ' + str (cageSet.lickIRQ) + ":")
            elif lick == 0:
                inputStr= input('No Touches detected in 10 seconds. Do you want to change IRQ pin, currently ' + str (cageSet.lickIRQ) + ":")
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                self.resetDetector()
                GPIO.cleanup (self.IRQ_PIN)
                cageSet.lickIRQ = int (input('Enter New Lick Detector IRQ pin:'))
                self.IRQ_PIN = cageSet.lickIRQ
                GPIO.setup(self.IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)        
       

class Simple_Logger (object):
    """
    A class to do simple logging of licks, used ig no data logger is passed to lickdetector constructor
    """
    
    def __init__(self, logFP):
        """
        takes file pointer to a file opened for writing
        If file ponter is none, will just write to shell
        """
        self.logFP = logFP

    
    def writeToLogFile(self, event):
        """
        Writes time of lick to shell, and to a file, if present, in AHF_dataLogger format
        """
        outPutStr = '{:013}'.format(0)
        logOutPutStr = outPutStr + '\t' + '{:.2f}'.format (time ())  + '\t' + event +  '\t' + datetime.fromtimestamp (int (time())).isoformat (' ')
        printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
        print (printOutPutStr)
        if self.logFP is not None:
            self.logFP.write(logOutPutStr + '\n')
            self.logFP.flush()
