#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM # abstract base class for servo-driver headfixers using PWM
import Adafruit_PCA9685 # the PCA9685 module drives the external PCA9685 stepper motor driver IC on the i2c bus

class AHF_HeadFixer_PWM_PCA9685 (AHF_HeadFixer_PWM):

    def __init__(self, cageSet):
        super().__init__(cageSet)
        self.pwm = Adafruit_PCA9685.PCA9685 (address=cageSet.servoAddress)
        self.pwm.set_pwm_freq (90) # 40-1000Hz
        self.releaseMouse()

    def set_value (self, servoPosition):
        self.pwm.set_pwm(0, 0, servoPosition)
        
    @staticmethod
    def configDict_read (cageSet, configDict):
        super(AHF_HeadFixer_PWM_PCA9685).configDict_read (cageSet, configDict)
        cageSet.servoAddress = int(configDict.get('Servo Address', 0x40))

        
    @staticmethod
    def configDict_set(cageSet,configDict):
        super(AHF_HeadFixer_PWM_PCA9685, AHF_HeadFixer_PWM_PCA9685).configDict_set(cageSet,configDict)
        configDict.update ({'Servo Address':cageSet.servoAddress,})

    @staticmethod
    def config_user_get (cageSet):
        super(AHF_HeadFixer_PWM_PCA9685, AHF_HeadFixer_PWM_PCA9685).config_user_get (cageSet)
        userResponse = input("Servo I2C Address, in Hexadecimal, or enter for default 0x40: ")
        if userResponse == '':
            userResponse = '0x40'
        userResponse = int (userResponse, 16)
        cageSet.servoAddress = userResponse


    @staticmethod
    def config_show(cageSet):
        rStr = super(AHF_HeadFixer_PWM_PCA9685, AHF_HeadFixer_PWM_PCA9685).config_show(cageSet)
        rStr += '\n\tServoDriver I2C Address, in Hexadecimal, =' + hex(cageSet.servoAddress) 
        return rStr

