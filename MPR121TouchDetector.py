#! /usr/bin/python
#-*-coding: utf-8 -*-

from Adafruit_MPR121 import MPR121
import RPi.GPIO as GPIO

"""
Code to use the MPR121 capacitive touch sensor to log touches, while ignoring 'un-touch' events
For continuous logging, a background task firing from the IRQ pin on the MPR121 can be installed with add_event_detect from RPi.GPIO.

Adafruit_MPR121 requires the Adafuit MPR121 library which, in turn,
requires the Adafuit GPIO library:
git clone https://github.com/adafruit/Adafruit_Python_MPR121 
git clone https://github.com/adafruit/Adafruit_Python_GPIO

NOTE :
Adafruit_Python_MPR121 has been deprecated. Adafruit has a new module for mpr121 using CircuitPython at github.com/adafruit/Adafruit_CircuitPython_MPR121
but this requires the whole CircuitPython install, which is rather large. It may be worth switching to this in the future.
"""

from time import time, sleep

from array import array




gTouchDetector = None
gTouched =0
gtouches = array('L'[0]*11)

"""
Global reference to touchDetector for interacting with touchDetector callback, will be set when touchDetetctor object is setup
Global reference to gTouched, bitwise-status of which pins are touched
Global reference to gTouches, the array of counts of touch events, which can be updated from the callback
"""

def touchDetectorCallback (channel):
    """
    touch Detetctor Callback, triggered by IRQ pin. mpr121 sets IRQ pin high whenever the touched/untouched state of any of the
    antenna pins changes. Calling mpr121.touched () sets the IRQ pin low again. mpr121.touched() returns a 12-but value
    where each bit  represents a pin, with a value of 1 being touched and 0 being not touched.
    This callback updates object field for touches, adds new touches to the array of touches used for counting touches,
    and possibly logs touchs. Callback tracks only touches, not un-touches, by keeping track of last touches
    
    """
    global gTouchDetector
    global gTouched
    gTouched = gTouchDetector.touched()
    # compare current touches to previous touches to find new touches
    pinBitVal =1
    for i in range (0,11):
        if (touches & pinBitVal) and not (gTouchDetector.prevTouches & pinBitVal):
            gTouchDetector.touchArray [i] +=1
            if gTouchDetector.isLogging:
                gTouchDetector.dataLogger.writeToLogFile(gtouchDetector.tagReader.readTag(), 'touch:' + str (i))
        pinBitVal *= 2
    gtouchDetector.prevTouches = touches


class TouchDetector (MPR121):
    def __init__(self, I2Caddr, touchThesh, unTouchThresh):
        super.__init__()
        self.begin(address =I2Caddr)
        self.set_thresholds (touchThesh, unTouchThresh)
         # state of touches from one invocation to next, used in callback to separate touches from untouches
        self.prevTouches = self.touched()


    def installCallback (self, IRQpin, callBackFunc = touchDetectorCallback):
        global gLickDetector
        gLickDetector = self
        # set up IRQ interrupt function. GPIO.setmode may already have been called, but call it again anyway
        GPIO.setmode (GPIO.BCM)
        GPIO.setup(IRQpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect (self.pin, GPIO.FALLING)
        GPIO.add_event_callback (self.pin, callBackFunc) 
    
