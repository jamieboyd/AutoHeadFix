#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
import RPi.GPIO as GPIO
from time import sleep

class AHF_HeadFixer_Pistons(AHF_HeadFixer):
    pistonsPinDef = 19

    @staticmethod
    def config_user_get (configDict = {}):
        pistonsPin = configDict.get ('pistonsPin', AHF_HeadFixer_Pistons.pistonsPinDef)
        userResponse = input('GPIO pin used to activate pistons (currently {:d}): '.format (pistonsPin))
        if userResponse != '':
            pistonsPin = int (userResponse)
        configDict.update({'pistonsPin' : pistonsPin})
        return configDict


    def setup (self):
        self.pistonsPin = self.configDict.get ('pistonsPin')
        GPIO.setmode(GPIO.BCM)
        GPIO.setup (self.pistonsPin, GPIO.OUT, initial = GPIO.LOW)
        
        
    def fixMouse(self):
        GPIO.output(self.pistonsPin, GPIO.HIGH)

    def releaseMouse(self):
        GPIO.output(self.pistonsPin, GPIO.LOW)

    def test (self, cageSet):
        inputStr = 'Yes'
        while inputStr[0] == 'y' or inputStr[0] == "Y":
            print ('Pistons Solenoid energizing for 2 sec.')
            GPIO.output(self.pistonsPin, GPIO.HIGH)
            sleep (2)
            GPIO.output(self.pistonsPin, GPIO.LOW)
            inputStr=input ('Pistons Solenoid de-energized.\nDo you want to change the Pistons Solenoid Pin, currently {}:'.format (self.pistonsPin))
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                GPIO.cleanup (self.pistonsPin)
                self.pistonsPin = int (input('Enter New Pistons Solenoid Pin:'))
                GPIO.setup (self.pistonsPin, GPIO.OUT)
                GPIO.output(self.pistonsPin, GPIO.LOW)
                cageSet.headFixerDict.update({'pistonsPin' : pistonsPin})