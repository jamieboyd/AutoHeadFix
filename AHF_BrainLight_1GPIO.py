#! /usr/bin/python3
#-*-coding: utf-8 -*-
import RPi.GPIO as GPIO
from time import sleep

from AHF_BrainLight import AHF_BrainLight

class AHF_BrainLight_1GPIO (AHF_BrainLight):

    @staticmethod
    def about():
        return 'Simplest brain illumination, toggles a single GPIO pin controlling an LED current driver.'
    
    @staticmethod
    def config_user_get (starterDict = {}):
        ledPin = starterDict.get ('ledPin', 23)
        result = input('Enter the GPIO pin connected to the blue LED for brain camera illumination, currently %d:' % ledPin)
        if result != '':
            ledPin = int(result)
        starterDict.update ({'ledPin':ledPin})
        return starterDict

    def __init__(self, settingsDictP):
        """
        initialization of a brain lighter, reading data from a settings dictionary
        """
        self.settingsDict = settingsDictP
        self.setup()

    def setup (self):
        """
        does hardware initialization of a brain lighter with (possibly updated) info in self.settingsDict
        """
        self.ledPin = self.settingsDict.get ('ledPin')
        GPIO.setmode(GPIO.BCM)
        GPIO.setup (self.ledPin, GPIO.OUT)


    def hardwareTest (self):
        self.onForStim()
        print ('Turning blue LED ON for two seconds....')
        sleep (2)
        print ('Turning blue LED OFF.')
        self.offForStim ()
        result = input ('Do you wish to edit brain light settings?')
        if result [0] == 'y' or result [0] == 'Y':
            self.settingsDict.update(AHF_BrainLight_1GPIO.config_user_get (self.settingsDict))
            self.setup ()

    def onForStim (self):
        GPIO.output (self.ledPin, GPIO.HIGH)


    def offForStim (self):
        GPIO.output (self.ledPin, GPIO.LOW)


