#! /usr/bin/python
#-*-coding: utf-8 -*-

"""
Code to use the MPR121 capacitive touch sensor from Adafruit to count/log touches, while ignoring 'un-touch' events, by way of a
threaded callback, installed with add_event_detect from RPi.GPIO, firing from the IRQ pin on the MPR121.

Adafruit_MPR121 requires the Adafuit MPR121 library which, in turn, requires the Adafuit GPIO library:
git clone https://github.com/adafruit/Adafruit_Python_MPR121 
git clone https://github.com/adafruit/Adafruit_Python_GPIO

NOTE :
Adafruit_Python_MPR121 has been deprecated. Adafruit has a new module for mpr121 using CircuitPython at github.com/adafruit/Adafruit_CircuitPython_MPR121
but this requires the whole CircuitPython install, which is rather large. It may be worth switching to this in the future.
"""

from Adafruit_MPR121 import MPR121
import RPi.GPIO as GPIO

from array import array
from time import time

"""
Touch Detector callback, triggered by IRQ pin.  The MPR121 sets the IRQ pin high whenever the touched/untouched state of any of the
antenna pins changes. Calling MPR121.touched () sets the IRQ pin low again.  MPR121.touched() returns a 12-but value
where each bit represents a pin, with a value of 1 being touched and 0 being not touched. The callback tracks only touches, 
not un-touches, by keeping track of last touches. The callback either counts touches on a set of channels, or saves timestamps of touches
on a set of channels, or calls a supplied custom function with the touched channel.
"""
gTouchDetector = None        # global reference to touchDetector for interacting with touchDetector callbacks

def touchDetectorCallback (channel):
    global gTouchDetector
    touches = gTouchDetector.touched()
    # compare current touches to previous touches to find new touches
    for channel in gTouchDetector.touchChans:
        chanBits = 2**channel
        if (touches & chanBits) and not (gTouchDetector.prevTouches & chanBits):
            if gTouchDetector.callbackMode & TouchDetector.callbackCountMode:
                gTouchDetector.touchCounts [channel] +=1
            if gTouchDetector.callbackMode & TouchDetector.callbackTimeMode:
                gTouchDetector.touchTimes.get(channel).append (time())
            if gTouchDetector.callbackMode & TouchDetector.callbackCustomMode:
                gTouchDetector.customCallback (channel)
    gTouchDetector.prevTouches = touches

class TouchDetector (MPR121):
    """
    TouchDetector inherits from Adafruit's MPR121 capacitive touch sensor code 
    """
    callbackOff = 0         # callback function not installed
    callbackSetTouch =1     # callback sets state of touches (all other modes need this set as well)
    callbackCountMode = 3   # callback counts licks on set of channels in touchChans
    callbackTimeMode = 5    # callback records time of each touch for each channel in touchChans 
    callbackCustomMode = 9  # callback calls custom function with touched channel
    
    def __init__(self, I2Caddr, touchThresh, unTouchThresh):
        super.__init__()
        self.setup (I2Caddr, touchThresh, unTouchThresh)

    def setup (I2Caddr, touchThresh, unTouchThresh):
        self.begin(address =I2Caddr)
        self.set_thresholds (touchThresh, unTouchThresh)
         # state of touches from one invocation to next, used in callback to separate touches from untouches
        self.prevTouches = self.touched()
        # an array of ints to count touches for each channel.
        self.touchCounts = array ('i', [0]*12)
        # a tuple of channel numbers to monitor
        self.touchChans = ()
        # a dictionary of lists to capture times of each lick on each channel
        self.touchTimes = {}
        # callback mode, for counting touches or capturing touch times
        self.callbackMode = TouchDetector.callbackOff
        # custom callback function, called from main callback function
        self.customCallback = None

    def installCallback (self, IRQpin, chanTuple, callbackMode):
        global gLickDetector
        gLickDetector = self
        # set up IRQ interrupt function. GPIO.setmode may already have been called, but call it again anyway
        GPIO.setmode (GPIO.BCM)
        GPIO.setup(IRQpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect (IRQpin, GPIO.FALLING)
        GPIO.add_event_callback (IRQpin, touchDetectorCallback)
        self.touchChans = chanTuple
        self.touchTimes = {}
        for chan in self.touchChans:
            self.touchTimes.update(chan : [])
        self.callbackMode = callbackMode

    def addCustomCallback (customCallBack)
        self.customCallback = customCallBack
        self.callbackMode = self.callbackMode | TouchDetector.callbackCustomMode

    def removeCallback (self, IRQpin):
        GPIO.remove_event_detect (IRQpin)
        GPIO.cleanup (IRQpin)
        self.callbackMode = TouchDetector.callbackOff

    def resetCount (self):
        """
        Zeros the array that stores counts for each channel, and makes sure callback is filling the array for requested channels
        """
        for i in range (0,12):
            self.touchCounts [i] = 0
       self.callbackMode = self.callbackMode | TouchDetector.callbackCountMode

    def getCount (self):
        """
        returns a list where each member is the number of touches for that channel in the global array
        call resetCount, wait a while for some touches, then call getCount
        """
        results = []
        for channel in self.touchChans:
            results.append (self.touchCounts [channel])
        return results

    def resetTimes (self):
        for chan in self.touchChans:
            self.touchTimes.update(chan : [])
        self.callbackMode = self.callbackMode | TouchDetector.callbackTimeMode

    def getTimes (self):
        return self.touchTimes

    def waitForTouch (self, timeOut_secs, setTouchMode, startFromZero=False):
        """
        Waits for a touch on any channel. Returns channel that was touched, or 0 if timeout expires with no touch,
        or -1 if startFromZero was True and the detector was touched for entire time
         """
        if setTouchMode:
            self.callbackMode =TouchDetector.callbackSetTouch
        endTime = time() + timeOut_secs
        if self.prevTouches == 0: # no touches now, wait for first touch, or timeout expiry
            while self.prevTouches ==0 and time() < endTime:
                sleep (0.05)
            return self.prevTouches
        else: #touches already registered
            if not startFromZero: # we are done already
                return self.prevTouches
            else: # we first wait till there are no touches, or time has expired
                while self.prevTouches > 0 and time() < endTime:
                    sleep (0.05)
                if time() > endTime: # touched till timeout expired
                    return -1
                else: # now wait for touch or til timeout expires
                    while self.prevTouches == 0 and time() < endTime:
                        sleep (0.05)
                    return self.prevTouches # will be the channel touched, or 0 if no touches till timeout expires



