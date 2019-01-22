#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_ContactCheck import AHF_ContactCheck
import RPi.GPIO as GPIO

class AHF_ContactCheck_BeamBreak (AHF_ContactCheck):


    @staticmethod
    def about ():
        return 'Beam-Break contact checker for Adafruit IR Beam Break Sensors'
    
    @staticmethod
    def config_user_get ():
        contactPin = int (input ('Enter the GPIO pin connected to the IR beam-breaker:'))
        contactDict={'contactPin': contactPin}
        return contactDict


    def __init__ (self, ContactCheckDict):
        self.contactDict = ContactCheckDict
        self.contactPin = self.contactDict.get ('contactPin', 21)
        self.setup()


    def setup (self):
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.cleanup (self.contactPin)
        GPIO.setup (self.contactPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)


    def checkContact(self):
        if (GPIO.input (self.contactPin)== GPIO.HIGH):
            return True
        else:
            return False

    def waitForContact(self, timeOutSecs):
        if GPIO.wait_for_edge (self.contactPin, GPIO.FALLING, timeout= timeOutSecs) is None:
            return False
        else:
            return True


    def hardwareTest (self):
        pass

        
