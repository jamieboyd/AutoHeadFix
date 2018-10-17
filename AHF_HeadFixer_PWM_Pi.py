#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM
from AHF_CageSet import AHF_CageSet
from PTPWM import PTPWM, PWM_simple
from time import sleep

class AHF_HeadFixer_PWM_Pi (AHF_HeadFixer_PWM):

    def __init__(self, cageSet):
        super().__init__(cageSet)
        PTPWM.set_clock (90, 4096)
        self.pwm =  PWM_simple(cageSet.pwmChan, PTPWM.PWM_MARK_SPACE, 4096)
        self.pwm.set_PWM (self.servoReleasedPosition)
        self.pwm.set_enable (1)
        

    def setPWM (self, servoPosition):
        self.pwm.set_PWM (servoPosition)

    @staticmethod
    def configDict_read (cageSet,configDict):
        super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).configDict_read (cageSet, configDict)
        cageSet.pwmChan = int(configDict.get('PWM Channel', 0))

    @staticmethod
    def configDict_set(cageSet,configDict):
        super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).configDict_set(cageSet,configDict)
        configDict.update ({'PWM Channel':cageSet.pwmChan,})

    @staticmethod
    def config_user_get (cageSet):
        super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).config_user_get (cageSet)
        cageSet.pwmChan = int (input ("PWM channel to use for servo: (0 on GPIO-18 or 1 on GPIO-19): "))
        
    @staticmethod
    def config_show(cageSet):
        rStr = super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).config_show(cageSet)
        rStr += '\n\tPWM channel used for servo:'
        if cageSet.pwmChan == 0:
            rStr += '0 on GPIO-18'
        elif cageSet.pwmChan ==1:
            rStr += '1 on GPIO-19'
        return rStr

if __name__ == "__main__":
    from time import sleep
    from AHF_CageSet import AHF_CageSet
    from AHF_HeadFixer import AHF_HeadFixer
    cageSettings = AHF_CageSet ()
    cageSettings.edit()
    cageSettings.save()
    headFixer=AHF_HeadFixer.get_class (cageSettings.headFixer) (cageSettings)
    headFixer.releaseMouse()
    sleep (1)
    headFixer.fixMouse()
    sleep (1)
    headFixer.releaseMouse()
