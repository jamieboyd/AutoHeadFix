#! /usr/bin/python3
#-*-coding: utf-8 -*-
import RPi.GPIO as GPIO
from time import sleep
from _thread import start_new_thread
from AHF_BrainLight import AHF_BrainLight

class AHF_BrainLight_1GPIO (AHF_BrainLight):
    
    defaultPin = 23 # default GPIO pin number

    @staticmethod
    def about():
        return 'Simplest brain illumination, toggles a single GPIO pin controlling an LED current driver.'
    
    @staticmethod
    def config_user_get (starterDict = {}):
        AHF_BrainLight.config_user_get (starterDict)
        ledPin = starterDict.get ('ledPin', AHF_BrainLight_1GPIO.defaultPin)
        result = input('Enter the GPIO pin connected to the blue LED for brain camera illumination, currently %d:' % ledPin)
        if result != '':
            ledPin = int(result)
        starterDict.update ({'ledPin':ledPin})
        return starterDict

    def setup (self):
        """
        does hardware initialization of a brain lighter with (possibly updated) info in self.settingsDict
        """
        self.ledPin = self.settingsDict.get ('ledPin')
        self.ledDelay = self.settingsDict.get ('ledDelay')
        hasGPIO = True
        try:
            GPIO.setup (self.ledPin, GPIO.OUT)
        except RuntimeError as e:
            print (str(e))
            hasGPIO = False
        return hasGPIO
        

    @staticmethod
    def onThread (sleepTime, ledPin):
        sleep (sleepTime)
        GPIO.output (ledPin, GPIO.HIGH)


    def setdown (self):
        GPIO.cleanup (self.ledPin)


    def onForStim (self):
        if self.ledDelay > 0:
            start_new_thread (self.onThread, (self.ledDelay,self.ledPin))
        else:
            GPIO.output (self.ledPin, GPIO.HIGH)

    def offForStim (self):
        if self.ledDelay > 0:
            sleep (self.ledDelay)
        GPIO.output (self.ledPin, GPIO.LOW)


