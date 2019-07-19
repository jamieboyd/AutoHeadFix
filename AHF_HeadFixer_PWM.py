#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_HeadFixer import AHF_HeadFixer
from time import sleep

class AHF_HeadFixer_PWM (AHF_HeadFixer, metaclass = ABCMeta):
    """
    abstract base class for servo-driver headfixers using Pulse Width Modulation, via built-in PWM or by an external driver
    Only methods that needs to be provided by sub-classes are setup and set_value method, although additional config
    information is expected through config_user_get
    """
    servoReleasedPositionDef = 650
    servoFixedPositionDef = 475

    @staticmethod
    def config_user_get (configDict = {}):
        """
        querries user to geta  dictionary of settings for PWM
        :param configDict: starter dictionary to fillout with setings
        :returns: the same dictionary, filled in or edited
        """
        servoReleasedPosition = configDict.get ('servoReleasedPosition', AHF_HeadFixer_PWM.servoReleasedPositionDef)
        tempInput = input('Servo Released Position (0-4095, currently {:d}):'.format (servoReleasedPosition))
        if tempInput != '':
            servoReleasedPosition = int(tempInput)
        servoFixedPosition = configDict.get ('servoFixedPosition', AHF_HeadFixer_PWM.servoFixedPositionDef)
        tempInput = input('Servo Fixed Position (0-4095, currently {:d}):'.format (servoFixedPosition))
        if tempInput != '':
            servoFixedPosition = int(tempInput)
        configDict.update({'servoReleasedPosition' : servoReleasedPosition, 'servoFixedPosition' : servoFixedPosition})
        return configDict


    @abstractmethod
    def setup (self):
        """
        initializes released and fixed positions for the servo
        """
        self.servoReleasedPosition = self.configDict.get ('servoReleasedPosition', AHF_HeadFixer_PWM.servoReleasedPositionDef)
        self.servoFixedPosition = self.configDict.get ('servoFixedPosition', AHF_HeadFixer_PWM.servoFixedPositionDef)
        self.configDict.update({'servoReleasedPosition' : self.servoReleasedPosition, 'servoFixedPosition' : self.servoFixedPosition})


    @abstractmethod
    def set_value (self, servoPosition):
        """
        Abstract method to set a value on the servo, subclasses must provide this for themselves
        """
        pass


    def fixMouse(self):
        """
        tells the servo to go to the stored fixed position
        """
        self.set_value (self.servoFixedPosition)


    def releaseMouse(self):
        """
        Tells the servo to go to the stored released position
        """
        self.set_value (self.servoReleasedPosition)


    def test (self, cageSet):
        """"
        run by hardware tester, allows user to set and test fixed and released positions
        """
        inputStr = 'Yes'
        while inputStr[0] == 'y' or inputStr[0] == "Y":
            print ('PWM moving to Head-Fixed position for 2 seconds')
            self.fixMouse()
            sleep (2)
            print ('PWM moving to Released position')
            self.releaseMouse()
            inputStr= input('Do you want to change fixed position, currently {}, or released position, currently {}:'.format (self.servoFixedPosition,self.servoReleasedPosition))
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                newValStr = input('Enter New PWM Fixed Position, or just enter to keep at {}:'.format(self.servoFixedPosition))
                if newValStr != '':
                    self.servoFixedPosition = int (newValStr)
                newValStr = input('Enter New PWM Released Position, or just enter to keep at {}:'.format(self.servoReleasedPosition))
                if newValStr != '':
                    self.servoReleasedPosition = int (newValStr)
                cageSet.headFixDict.update ({'servoReleasedPosition' : self.servoReleasedPosition, 'servoFixedPosition' : self.servoFixedPosition})

