#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
import RPi.GPIO as GPIO
from time import sleep

class AHF_HeadFixer_Pistons(AHF_HeadFixer):
    """
    Head fixer using solenoid-driven pistons to push head bar against front plate
    a single GPIO output triggers a driver of some kind to energize solenoids
    """
    @staticmethod
    def about():
        return 'Single GPIO output using RPi.GPIO triggers a driver of some kind to energize solenoids that push headbar'
    
    def __init__(self, headFixerDict):
        """
        init data is a single GPIO pi, which will be configured for output
        pin number is copied from task, where it will have been loaded from configDict
        """
        self.pistonsPin = headFixerDict.get ('pistonsPin')
        self.setup()

    def setup (self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.cleanup (self.pistonsPin)
        GPIO.setup (self.pistonsPin, GPIO.OUT, initial = GPIO.LOW)

    def fixMouse(self):
        """
        sets GPIO pin high to trigger pistons
        """
        GPIO.output(self.pistonsPin, GPIO.HIGH)

    def releaseMouse(self):
        """
        sets GPIO pin low to retract pistons
        """
        GPIO.output(self.pistonsPin, GPIO.LOW)
        
                   
    @staticmethod
    def config_user_get ():
        """
        Querries user for pin number for piston, returns dictionary 
        """
        pin= int(input ('Enter the GPIO pin connected to the Head Fixing pistons:'))
        return {'pistonsPin': pin,}

    
    def hardwareTest (self, headFixDict):
        print ('Pistons Solenoid energizing for 2 sec')
        GPIO.output(self.pistonsPin, GPIO.HIGH)
        sleep (2)
        GPIO.output(self.pistonsPin, GPIO.LOW)
        inputStr=input ('Pistons Solenoid de-energized.\nDo you want to change the Pistons Solenoid Pin (currently ' + str(cageSet.pistonsPin) + ')?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.pistonsPin = int (input('Enter New Pistons Solenoid Pin:'))
            headFixDict.update ({'pistonsPin': self.pistonsPin})
            self.setup()
