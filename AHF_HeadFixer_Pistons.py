#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
import RPi.GPIO as GPIO
from time import sleep

class AHF_HeadFixer_Pistons(AHF_HeadFixer):

    def __init__(self, cageSet):
        self.pistonsPin = cageSet.pistonsPin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup (self.pistonsPin, GPIO.OUT, initial = GPIO.LOW)

    def fixMouse(self):
        GPIO.output(self.pistonsPin, GPIO.HIGH)

    def releaseMouse(self):
        GPIO.output(self.pistonsPin, GPIO.LOW)
        
    @staticmethod
    def configDict_read (cageSet, configDict):
        cageSet.pistonsPin= int(configDict.get('Pistons Pin'))

    @staticmethod
    def configDict_set(cageSet,configDict):
        configDict.update ({'Pistons Pin':cageSet.pistonsPin})
                   
    @staticmethod
    def config_user_get (cageSet):
        cageSet.pistonsPin = int(input ('Enter the GPIO pin connected to the Head Fixing pistons:'))
        
    @staticmethod
    def config_show(cageSet):
        return 'Pistons Solenoid Pin=' +  str (cageSet.pistonsPin)

    def test (self, cageSet):
        inputStr = 'Yes'
        while inputStr[0] == 'y' or inputStr[0] == "Y":
            print ('Pistons Solenoid energizing for 2 sec.')
            GPIO.output(cageSet.pistonsPin, GPIO.HIGH)
            sleep (2)
            GPIO.output(cageSet.pistonsPin, GPIO.LOW)
            inputStr=input ('Pistons Solenoid de-energized.\nDo you want to change the Pistons Solenoid Pin, currently {}:'.format (cageSet.pistonsPin))
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                GPIO.cleanup (cageSet.pistonsPin)
                cageSet.pistonsPin = int (input('Enter New Pistons Solenoid Pin:'))
                self.pistonsPin = cageSet.pistonsPin
                GPIO.setup (cageSet.pistonsPin, GPIO.OUT)
