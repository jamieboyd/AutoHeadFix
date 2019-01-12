#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM
import ptPWM
from time import sleep

class AHF_HeadFixer_PWM_Pi (AHF_HeadFixer_PWM):

    @staticmethod
    def about():
        return 'uses ptPWM module to drive Pi\'s own PWM peripheral to control servo motor to puch head bar' 
    

    def __init__(self, headFixerDict):
        # servo released position and fixed position are set
        super().__init__(headFixerDict)
        self.pwmChan = headFixerDict.get('pwmChan')

    def setup (self):
        self.pwm_ptr = ptPWM.newThreadless(90, 4096)
        ptPWM.threadlessAddChan(self.pwm_ptr, self.pwmChan, 1, 0, 0)
        ptPWM.threadlessSetValue(self.pwm_ptr, self.servoReleasedPosition, self.pwmChan)
        ptPWM.threadlessSetAble (self.pwm_ptr, 1, self.pwmChan)

    def setPWM (self, servoPosition):
        ptPWM.threadlessSetValue(self.pwm_ptr, servoPosition, self.pwmChan)


    @staticmethod
    def config_user_get ():
        headFixDict = super(AHF_HeadFixer_PWM_Pi, AHF_HeadFixer_PWM_Pi).config_user_get ()
        pwmChan = int (input ("PWM channel to use for servo: (1 on GPIO-18 or 2 on GPIO-19): "))
        headFixDict.update ({'pwmChan': pwmChan})       
