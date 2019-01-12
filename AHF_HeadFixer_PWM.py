#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_HeadFixer import AHF_HeadFixer
from time import sleep

class AHF_HeadFixer_PWM (AHF_HeadFixer, metaclass = ABCMeta):
    """
    Abstract class for PWM-based head fixers for servo motors. As long as your subclass maps your PWM range onto
    the appropriate pulse width for the servo, you should be good to go.
    """
    hasLevels = False
    numLevels =8
    ##################################################################################
    #part 1: three main methods of initing, fixing, and releasing, only initing is different for different PWM methods
    def __init__(self, headFixerDict):
        self.servoReleasedPosition = headFixerDict.get ('servoReleasedPosition')
        self.servoFixedPosition = headFixerDict.get ('servoFixedPosition')
        self.servoIncrement = (self.servoFixedPosition - self.servoReleasedPosition)/self.numLevels
        self.level = self.numLevels
        
    @abstractmethod
    def setup (self, task):
        pass

    
    # with progressive head fixing. typical servo values 325 =fixed, 540 = released
    # self.numLevels different levels of fixing tightness, with 0 being released position
    def fixMouse(self):
        self.setPWM (int(self.servoReleasedPosition + (self.servoIncrement * self.level)))
                
            
    def releaseMouse(self):
        self.setPWM (self.servoReleasedPosition)

    # each PWM subclass must implement its own code to set the pulse width
    @abstractmethod
    def setPWM (self, servoPosition):
        pass


    def level_set_level (self, level):
        self.level = min (self.numLevels, max (0, level))
  
    ##################################################################################
    #abstact methods each PWM headfixer class must implement
    #part 2: static functions for reading, editing, and saving ConfigDict from/to cageSet
       
    @staticmethod
    def config_user_get ():
        servoReleasedPosition = int(input("Servo Released Position (0-4095): "))
        servoFixedPosition = int(input("Servo Fixed Position (0-4095): "))
        return {'servoReleasedPosition' : servoReleasedPosition, 'servoFixedPosition' : servoFixedPosition}

    
    def hardwareTest (self, headFixDict):
        print ('servo moving to Head-Fixed position for 3 seconds')
        self.fixMouse()
        sleep (3)
        print ('servo moving to Released position')
        self.releaseMouse()
        inputStr= input('Do you want to change fixed position, currently ' + str (self.servoFixedPosition) + ', or released position, currently ' + str(self.servoReleasedPosition) + ':')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.servoFixedPosition = int (input('Enter New servo Fixed Position:'))
            self.servoReleasedPosition = int (input('Enter New servo Released Position:'))
            self.servoIncrement = (self.servoFixedPosition - self.servoReleasedPosition)/self.numLevels
            headFixDict.update({'servoReleasedPosition' : servoReleasedPosition, 'servoFixedPosition' : servoFixedPosition})
    

if __name__ == "__main__":
    AHF_HeadFixer.funcForMain()
