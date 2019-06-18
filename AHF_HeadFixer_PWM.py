#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_HeadFixer import AHF_HeadFixer
from AHF_CageSet import AHF_CageSet
from PTPWM import PTPWM, PTPWMsimp
from time import sleep

class AHF_HeadFixer_PWM (AHF_HeadFixer, metaclass = ABCMeta):

    def __init__(self, cageSet):
        self.servoReleasedPosition = cageSet.servoReleasedPosition
        self.servoFixedPosition = cageSet.servoFixedPosition

    @abstractmethod
    def set_value (self):
        pass 

    def fixMouse(self):
        self.pwm.set_value (self.servoFixedPosition)

    def releaseMouse(self):
        self.pwm.set_value (self.servoReleasedPosition)

    @staticmethod
    def configDict_read (cageSet,configDict):
        cageSet.pwmChan = int(configDict.get('PWM Channel', 0))
        cageSet.servoReleasedPosition = int(configDict.get('Released Servo Position', 815))
        cageSet.servoFixedPosition = int(configDict.get('Fixed Servo Position', 500))

    @staticmethod
    def configDict_set(cageSet,configDict):
        configDict.update ({'PWM Channel':cageSet.pwmChan, 'Released Servo Position':cageSet.servoReleasedPosition,'Fixed Servo Position':cageSet.servoFixedPosition})

    @staticmethod
    def config_user_get (cageSet):
        cageSet.pwmChan = int (input ("PWM channel to use for servo: (0 on GPIO-18 or 1 on GPIO-19): "))
        cageSet.servoReleasedPosition = int(input("Servo Released Position (0-4095): "))
        cageSet.servoFixedPosition = int(input("Servo Fixed Position (0-4095): "))
        
    @staticmethod
    def config_show(cageSet):
        rStr = 'PWM channel used for servo:'
        if cageSet.pwmChan == 0:
            rStr += '0 on GPIO-18'
        elif cageSet.pwmChan ==1:
            rStr += '1 on GPIO-19'
        rStr += '\n\tReleased Servo Position=' + str(cageSet.servoReleasedPosition) + '\n\tFixed Servo Position=' + str(cageSet.servoFixedPosition)
        return rStr
    

    
    def test (self, cageSet):
        print ('PWM moving to Head-Fixed position for 2 seconds')
        self.fixMouse()
        sleep (2)
        print ('PWM moving to Released position')
        self.releaseMouse()
        inputStr= input('Do you want to change fixed position, currently ' + str (cageSet.servoFixedPosition) + ', or released position, currently ' + str(cageSet.servoReleasedPosition) + ':')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            cageSet.servoFixedPosition = int (input('Enter New PWM Fixed Position:'))
            cageSet.servoReleasedPosition = int (input('Enter New PWM Released Position:'))
            self.servoReleasedPosition = cageSet.servoReleasedPosition
            self.servoFixedPosition = cageSet.servoFixedPosition


if __name__ == "__main__":
    from time import sleep
    hardWare = AHF_CageSet ()
    hardWare.edit()
    hardWare.save()

    s = AHF_HeadFixer_PWM (hardWare)
    s.fixMouse()
    sleep(5)
    s.releaseMouse()
