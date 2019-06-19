#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_HeadFixer import AHF_HeadFixer
from time import sleep

class AHF_HeadFixer_PWM (AHF_HeadFixer, metaclass = ABCMeta):
    """
    abstract base class for servo-driver headfixers using Pulse Width Modulation, via built-in PWM or by an external driver
    Only method that needs to be provided by sub-classes is the set_value method, although additional setup and config
    information is expected
    """
    def __init__(self, cageSet):
        """
        initializes released and fixed positions for the servo
        """
        self.servoReleasedPosition = cageSet.servoReleasedPosition
        self.servoFixedPosition = cageSet.servoFixedPosition

    @abstractmethod
    def set_value (self, servoPosition):
        """
        Abstract method to run the servo, subclasses must provide this for themselves
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

    @staticmethod
    def configDict_read (cageSet,configDict):
        """
        Static method to read fixed and released positions from the configuration dict into the cageSet object
        """
        cageSet.servoReleasedPosition = configDict.get('Released Servo Position')
        cageSet.servoFixedPosition = configDict.get('Fixed Servo Position', )

    @staticmethod
    def configDict_set(cageSet,configDict):
        configDict.update ({'Released Servo Position':cageSet.servoReleasedPosition,'Fixed Servo Position':cageSet.servoFixedPosition})

    @staticmethod
    def config_user_get (cageSet):
        cageSet.servoReleasedPosition = int(input("Servo Released Position (0-4095): "))
        cageSet.servoFixedPosition = int(input("Servo Fixed Position (0-4095): "))
        
    @staticmethod
    def config_show(cageSet):
        rStr = '\n\tReleased Servo Position=' + str(cageSet.servoReleasedPosition) + '\n\tFixed Servo Position=' + str(cageSet.servoFixedPosition)
        return rStr
    

    def test (self, cageSet):
        inputStr = 'Yes'
        while inputStr[0] == 'y' or inputStr[0] == "Y":
            print ('PWM moving to Head-Fixed position for 2 seconds')
            self.fixMouse()
            sleep (2)
            print ('PWM moving to Released position')
            self.releaseMouse()
            inputStr= input('Do you want to change fixed position, currently {}, or released position, currently {}:'.format (cageSet.servoFixedPosition,cageSet.servoReleasedPosition))
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                newValStr = input('Enter New PWM Fixed Position, or just enter to keep at {}:'.format(cageSet.servoFixedPosition))
                if newValStr != '':
                    cageSet.servoFixedPosition = int (newValStr)
                newValStr = input('Enter New PWM Released Position, or just enter to keep at {}:'.format(cageSet.servoReleasedPosition))
                if newValStr != '':
                    cageSet.servoReleasedPosition = int (newValStr)                            
                self.servoReleasedPosition = cageSet.servoReleasedPosition
                self.servoFixedPosition = cageSet.servoFixedPosition

