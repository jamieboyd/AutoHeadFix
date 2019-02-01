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
    hasLevels = True
    numLevels =8
    

    @staticmethod
    @abstractmethod
    def config_user_get (starterDict = {}):
        servoReleasedPosition = starterDict.get ('servoReleasedPosition', 540)
        response = input("Set Servo Released Position (0-4095: currently %d): " % servoReleasedPosition)
        if response != '':
            servoReleasedPosition = int(response)
        servoFixedPosition = starterDict.get ('servoFixedPosition', 325)
        response = input("Set Servo Fixed Position (0-4095: currently %d): " % servoFixedPosition)
        if response != '':
            servoFixedPosition = int(response)
        starterDict.update ({'servoReleasedPosition' : servoReleasedPosition, 'servoFixedPosition' : servoFixedPosition})
        return starterDict

    
    @abstractmethod
    def setup (self):
        self.servoReleasedPosition = self.settingsDict.get ('servoReleasedPosition')
        self.servoFixedPosition = self.settingsDict.get ('servoFixedPosition')
        if self.__class__.hasLevels:
            self.servoIncrement = (self.servoFixedPosition - self.servoReleasedPosition)/self.numLevels
    
    def fixMouse(self, mouse = None):
        if self.hasLevels and hasattr (mouse, 'HeadFixLevel'):
            self.setPWM (int(self.servoReleasedPosition + (self.servoIncrement * mouse.HeadFixLevel)))
        else:
            self.setPWM (self.servoFixedPosition)

    def releaseMouse(self):
        self.setPWM (self.servoReleasedPosition)


    # each PWM subclass must implement its own code to set the pulse width
    @abstractmethod
    def setPWM (self, servoPosition):
        pass


    # Head-Fixer hardware test overwritten to just modify fixed and released servo positions, other settings not likely to change
    def hardwareTest (self):
        print ('servo moving to Head-Fixed position for 3 seconds')
        self.fixMouse()
        sleep (3)
        print ('servo moving to Released position')
        self.releaseMouse()
        inputStr= input('Do you want to change fixed position (currently %d) or released position (currently %d)? ' % (self.servoFixedPosition ,self.servoReleasedPosition))
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.settingsDict = AHF_HeadFixer_PWM.config_user_get (self.settingsDict)
            self.servoReleasedPosition = self.settingsDict.get ('servoReleasedPosition')
            self.servoFixedPosition = self.settingsDict.get ('servoFixedPosition')

