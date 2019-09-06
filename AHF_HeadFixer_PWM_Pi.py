#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM
import ptPWM
from time import sleep

class AHF_HeadFixer_PWM_Pi(AHF_HeadFixer_PWM):
    defaultChannel = 1
    
    @staticmethod
    def about():
        return 'uses ptPWM module to drive Pi\'s own PWM peripheral to control servo motor to push head bar' 
    
    @staticmethod
    def config_user_get(starterDict = {}):
        starterDict.update(AHF_HeadFixer_PWM.config_user_get(starterDict))
        pwmChan = starterDict.get('pwmChan', AHF_HeadFixer_PWM_Pi.defaultChannel)
        response = input("PWM channel to use for servo:(1 on GPIO-18 or 2 on GPIO-19, currently %d): " % pwmChan)
        if response != '':
            pwmChan = int(response)
        starterDict.update({'pwmChan': pwmChan})
        return starterDict

    def setup(self):
        super().setup()
        self.pwmChan = self.settingsDict.get('pwmChan')
        hasFixer = True
        try:
            self.pwm_ptr = ptPWM.newThreadless(90, 4096)
            ptPWM.threadlessAddChan(self.pwm_ptr, self.pwmChan, 1, 0, 0)
            ptPWM.threadlessSetValue(self.pwm_ptr, self.servoReleasedPosition, self.pwmChan)
            ptPWM.threadlessSetAble(self.pwm_ptr, 1, self.pwmChan)
        except Exception as e:
            print(str(e))
            hasFixer = False
        return hasFixer

    def setdown(self):
        del self.pwm_ptr

    def setPWM(self, servoPosition):
        ptPWM.threadlessSetValue(self.pwm_ptr, servoPosition, self.pwmChan)


