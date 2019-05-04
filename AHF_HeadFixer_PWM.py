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
    defaultReleasePosition = 933
    defaultFixedPosition = 685

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

    def fixMouse(self, thisTag, resultsDict = {}, individualDict= {}):
        self.task.isFixTrial = settingsDict.get ('propHeadFix', self.propHeadFix) > random()
        hasContact = False
        if self.task.isFixTrial:
            if self.waitForMouse (): # contact was made
                self.setPWM (individualDict.get ('servoFixedPosition', self.servoFixedPosition))
                sleep (0.5)
                hasContact = self.task.contact
                if not hasContact: # tried to fix and failed
                    self.setPWM (self.servoReleasedPosition)
                self.hasMouseLog (hasContact, isFixTrial, resultsDict, settingsDict)
        else: # noFix trial, wait for contact and return
            hasContact = self.waitForMouse ()
            if hasContact:
                self.hasMouseLog (True, isFixTrial, resultsDict, settingsDict)
        return hasContact


    def releaseMouse(self, thisTag, resultsDict = {}, settingsDict= {}):
        self.setPWM (self.servoReleasedPosition)
        super().releaseMouse (thisTag, resultsDict, individualDict)

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
