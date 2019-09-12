#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
import RPi.GPIO as GPIO
from time import sleep
from random import random

class AHF_HeadFixer_Pistons(AHF_HeadFixer):
    """
    Head fixer using solenoid-driven pistons to push head bar against front plate
    a single GPIO output triggers a driver of some kind to energize solenoids
    """
    defaultPin = 12

    @staticmethod
    def about():
        return 'Single GPIO output triggers driver that energize solenoids that push headbar'

    @staticmethod
    def config_user_get(starterDict = {}):
        """
        Querries user for pin number for piston, returns dictionary
        """
        starterDict.update(AHF_HeadFixer.config_user_get(starterDict))
        pin = starterDict.get('pistonsPin', AHF_HeadFixer_Pistons.defaultPin)
        response = input('Enter the GPIO pin connected to the Head Fixing pistons, currently %d:' % pin)
        if response != '':
            pin = int(response)
        starterDict.update({'pistonsPin': pin})
        return starterDict

    def config_subject_get(self, starterDict = {}):
        return super().config_subject_get(starterDict)

    def config_user_subject_get(self, starterDict = {}):
        return super().config_user_subject_get(starterDict)

    def setup(self):
        hasFixer = True
        super().setup()
        self.pistonsPin = self.settingsDict.get('pistonsPin')
        try:
            GPIO.setup(self.pistonsPin, GPIO.OUT, initial = GPIO.LOW)
        except Exception as e:
            print(str(e))
            hasFixer = False
        return hasFixer


    def setdown(self):
        GPIO.cleanup(self.pistonsPin)


    def fixMouse(self, thisTag, resultsDict = {}, settingsDict= {}):
        """
        sets GPIO pin high to trigger pistons

        """
        self.task.isFixTrial = settingsDict.get('propHeadFix', self.propHeadFix) > random()
        hasContact = False
        if self.task.isFixTrial:
            if self.waitForMouse(): # contact was made
                GPIO.output(self.pistonsPin, GPIO.HIGH)
                sleep(0.5)
                hasContact = self.task.contact
                if not hasContact: # tried to fix and failed
                    GPIO.output(self.pistonsPin, GPIO.LOW)
                self.hasMouseLog(hasContact, self.task.isFixTrial, resultsDict, settingsDict)
        else: # noFix trial, wait for contact and return
            hasContact = self.waitForMouse()
            if hasContact:
                self.hasMouseLog(True, self.task.isFixTrial, resultsDict, settingsDict)
        return hasContact


    def releaseMouse(self, resultsDict = {},individualDict= {}):
        """
        sets GPIO pin low to retract pistons
        """
        if self.task.isFixTrial:
            GPIO.output(self.pistonsPin, GPIO.LOW)
        super().releaseMouse(resultsDict, individualDict)
