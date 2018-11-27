#! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
uses PCA9685 code from AdaFruit, install as follows
sudo apt-get install i2c-tools
sudo apt-get install python3-smbus
git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
git clone https://github.com/adafruit/Adafruit_Python_PCA9685.git

"""

# Import the PCA9685 module.
import Adafruit_PCA9685
from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM


class AHF_HeadFixer_PWM_PCA9685 (AHF_HeadFixer_PWM):

    def __init__(self, cageSet):
        super().__init__(cageSet)
        self.pwm = Adafruit_PCA9685.PCA9685 (address=cageSet.servoAddress)
        self.pwm.set_pwm_freq (90) # 40-1000Hz
        self.releaseMouse()

    def setPWM (self, servoPosition):
        self.pwm.set_pwm(0, 0, servoPosition)
        
    @staticmethod
    def configDict_read (cageSet, configDict):
        super(AHF_HeadFixer_PWM_PCA9685).configDict_read (cageSet, configDict)
        cageSet.servoAddress = int(configDict.get('Servo Address', 0x40))

        
    @staticmethod
    def configDict_set(cageSet,configDict):
        super(AHF_HeadFixer_PWM_PCA9685).configDict_set(cageSet,configDict)
        configDict.update ({'Servo Address':cageSet.servoAddress,})

    @staticmethod
    def config_user_get (cageSet):
        super(AHF_HeadFixer_PWM_PCA9685).config_user_get (cageSet)
        userResponse = input("Servo I2C Address, in Hexadecimal, or enter for default 0x40: ")
        if userResponse == '':
            userResponse = '0x40'
        userResponse = int (userResponse, 16)
        cageSet.servoAddress = userResponse


    @staticmethod
    def config_show(cageSet):
        rStr = super(AHF_HeadFixer_PWM_PCA9685).config_show(cageSet)
        rStr += '\n\tServoDriver I2C Address, in Hexadecimal, =' + hex(cageSet.servoAddress) 
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
