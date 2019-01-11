#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM
import ptPWM
from time import sleep

class AHF_HeadFixer_PWM_Pi (AHF_HeadFixer_PWM):

    def __init__(self, task):
        # servo released position and fixed position are set
        super().__init__(cageSet)
        self.pwmChan = task.pwmChan

    def setup (self):
        self.pwm_ptr = ptPWM.newThreadless(90, 4096)
        ptPWM.threadlessAddChan(self.pwm_ptr, self.pwmChan, 1, 0, 0)
        ptPWM.threadlessSetValue(self.pwm_ptr, self.servoReleasedPosition, self.pwmChan)
        ptPWM.threadlessSetAble (self.pwm_ptr, 1, self.pwmChan)

    def setPWM (self, servoPosition):
        ptPWM.threadlessSetValue(self.pwm_ptr, servoPosition, self.pwmChan)

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
        if cageSet.pwmChan == 0:
            rStr += '0 on GPIO-18'
        elif cageSet.pwmChan ==1:
            rStr += '1 on GPIO-19'
        return rStr

if __name__ == "__main__":
    from time import sleep
    from AHF_HeadFixer import AHF_HeadFixer
    cageSettings.edit()
    cageSettings.save()
    headFixer=AHF_HeadFixer.get_class (cageSettings.headFixer) (cageSettings)
    headFixer.releaseMouse()
    sleep (1)
    headFixer.fixMouse()
    sleep (1)
    headFixer.releaseMouse()
