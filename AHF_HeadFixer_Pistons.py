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
    def __init__(self, task):
        """
        init data is a single GPIO pi, which will be configured for output
        pin number iis copied from task, where it will have been loaded from configDict
        """
        self.pistonsPin = task.pistonsPin
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
    def configDict_read (task, configDict):
        """
        reads pistons pin number form dictionary and sets attribute in task
        """
        setattr (task, 'pistonsPin', int(configDict.get('Pistons Pin')))

    @staticmethod
    def configDict_set(task,configDict):
        """
        copies pin number from task to config dict
        """
        configDict.update ({'Pistons Pin':task.pistonsPin})
                   
    @staticmethod
    def config_user_get (task):
        """
        Querries user for pin number for piston, copies it to task
        """
        pin= int(input ('Enter the GPIO pin connected to the Head Fixing pistons:'))
        setattr (task, 'pistonsPin',pin)
        
    @staticmethod
    def config_show(task):
        """
        returns a string describing pin for solenoid pistons
        """
        return 'Pistons Solenoid Pin=' +  str (task.pistonsPin)
    
    def test (self, task):
        print ('Pistons Solenoid energizing for 2 sec')
        GPIO.output(task.pistonsPin, 1)
        sleep (2)
        GPIO.output(task.pistonsPin, 0)
        inputStr=input ('Pistons Solenoid de-energized.\nDo you want to change the Pistons Solenoid Pin (currently ' + str(cageSet.pistonsPin) + ')?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            task.pistonsPin = int (input('Enter New Pistons Solenoid Pin:'))
            self.pistonsPin = task.pistonsPin
            GPIO.setup (self.pistonsPin, GPIO.OUT)
