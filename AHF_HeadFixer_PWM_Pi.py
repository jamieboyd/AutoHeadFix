#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM # abstract base class for servo-driver headfixers using PWM
from PTPWM import PTPWM, PTPWMsimp # wraps the c module that controls the onboard PWM peripheral on the Pi

class AHF_HeadFixer_PWM_Pi (AHF_HeadFixer_PWM):
    """
    Head Fixer class that controls a servo motor with PWM using the Raspberry Pi's own
    PWM peripheral. Requires the ptPWM C module with PTPWM python wrapper, from GPIO_Thread
    """
    pwmChanDef = 1

    @staticmethod
    def config_user_get (configDict = {}):
        configDict = super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).config_user_get (configDict)
        pwmChan = configDict.get ('pwmChan', AHF_HeadFixer_PWM_Pi.pwmChanDef)
        tempInput = input('Enter channel used for PWM, 1 on GPIO 18, or 2 on GPIO 19 (currently {:d})'.format (pwmChan))
        if tempInput != '':
            pwmChan = int (tempInput)
        configDict.update({}'pwmChan' : 'pwmChan'})
        return configDict


    def setup (self):
        super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).setup()
        self.pwmChan = self.configDict.get ('pwmChan')
        self.pwm = PTPWMsimp (100, 4096)
        self.pwm.add_channel (self.pwmChan, PTPWM.PWM_MARK_SPACE,0,0)
        self.pwm.set_able (1, self.pwmChan)
        self.releaseMouse ()


    def set_value (self, servoPosition):
        self.pwm.set_value (servoPosition, self.pwmChan)
