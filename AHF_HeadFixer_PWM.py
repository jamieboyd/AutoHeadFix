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
    defaultReleasePosition = 540
    defaultFixedPosition = 325
    
    @staticmethod
    @abstractmethod
    def config_user_get (starterDict = {}):
        starterDict.update (AHF_HeadFixer.config_user_get(starterDict))
        servoReleasedPosition = starterDict.get ('servoReleasedPosition', AHF_HeadFixer_PWM.defaultReleasePosition)
        response = input("Set Servo Released Position (0-4095: currently %d): " % servoReleasedPosition)
        if response != '':
            servoReleasedPosition = int(response)
        servoFixedPosition = starterDict.get ('servoFixedPosition', AHF_HeadFixer_PWM.defaultFixedPosition)
        response = input("Set Servo Fixed Position (0-4095: currently %d): " % servoFixedPosition)
        if response != '':
            servoFixedPosition = int(response)
        starterDict.update ({'servoReleasedPosition' : servoReleasedPosition, 'servoFixedPosition' : servoFixedPosition})
        return starterDict


    def individualSettings (self, starterDict={}):
        """
        copies servo fixed position to dictionary - there is no reason to have different released positions per subject
        TO DO: add multiple headfixing levels, maybe progression based on resdults
        """
        starterDict.update ({'servoFixedPosition' : self.servoFixedPosition})
        return starterDict

    
    @abstractmethod
    def setup (self):
        super().setup()
        self.servoReleasedPosition = self.settingsDict.get ('servoReleasedPosition')
        self.servoFixedPosition = self.settingsDict.get ('servoFixedPosition')
        if self.__class__.hasLevels:
            self.servoIncrement = (self.servoFixedPosition - self.servoReleasedPosition)/self.numLevels
    
    def fixMouse(self, resultsDict = {}, individualDict= {}):
        self.setPWM (individualDict.get ('servoFixedPosition', self.servoFixedPosition))
        resultsDict.update ({'headFixes' : resultsDict.get('headFixes', 0) + 1})

    def releaseMouse(self, resultsDict = {}, settingsDict= {}):
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

