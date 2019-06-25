#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM # abstract base class for servo-driver headfixers using PWM
from PTPWM import PTPWM, PTPWMsimp # wraps the c module that controls the onboard PWM peripheral on the Pi
from time import sleep

class AHF_HeadFixer_PWM_Pi (AHF_HeadFixer_PWM):
    """
    Head Fixer class that controls a servo motor with PWM using the Raspberry Pi's own
    PWM peripheral. Requires the ptPWM C module with PTPWM python wrapper, from GPIO_Thread
    """
    AHF_HeadFixer_PWM_Pi.pwmChanDef = 1
    def __init__(self, cageSet):
        super().__init__(cageSet)
        if not hasattr (cageSet, 'pwmChan'):
            cageSet.pwmChan = AHF_HeadFixer_PWM_Pi.pwmChanDef
        self.pwmChan = cageSet.pwmChan
        self.pwm = PTPWMsimp (100, 4096)
        self.pwm.add_channel (self.pwmChan, PTPWM.PWM_MARK_SPACE,0,0)
        self.pwm.set_able (1, self.pwmChan)
        self.releaseMouse ()
        
    def set_value (self, servoPosition):
        self.pwm.set_value (servoPosition, self.pwmChan)

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
        cageSet.pwmChan = int (input ("PWM channel to use for servo: (1 on GPIO-18 or 2 on GPIO-19): "))
        
    @staticmethod
    def config_show(cageSet):
        rStr = super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).config_show(cageSet)
        rStr += '\n\tPWM channel used for servo:'
        if cageSet.pwmChan == 1:
            rStr += '1 on GPIO-18'
        elif cageSet.pwmChan ==2:
            rStr += '2 on GPIO-19'
        return rStr
