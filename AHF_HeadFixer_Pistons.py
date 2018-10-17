#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
import RPi.GPIO as GPIO
from time import sleep

class AHF_HeadFixer_Pistons(AHF_HeadFixer):

    def __init__(self, task):
        self.pistonsPin = task.pistonsPin
        GPIO.setup (self.pistonsPin, GPIO.OUT, initial = GPIO.LOW)

    def fixMouse(self):
        GPIO.output(self.pistonsPin, GPIO.HIGH)

    def releaseMouse(self):
        GPIO.output(self.pistonsPin, GPIO.LOW)
        
    @staticmethod
    def configDict_read (task, configDict):
        setattr (task, 'pistonsPin',int(configDict.get('Pistons Pin')))

    @staticmethod
    def configDict_set(task,configDict):
        configDict.update ({'Pistons Pin':task.pistonsPin})
                   
    @staticmethod
    def config_user_get (task):
        pin= int(input ('Enter the GPIO pin connected to the Head Fixing pistons:'))
        setattr (task, 'pistonsPin',pin)
        
    @staticmethod
    def config_show(task):
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
