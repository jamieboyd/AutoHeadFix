#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM # abstract base class for servo-driver headfixers using PWM
import Adafruit_PCA9685 # the PCA9685 module drives the external PCA9685 stepper motor driver IC on the i2c bus

class AHF_HeadFixer_PWM_PCA9685 (AHF_HeadFixer_PWM):
    servoAddressDef = 0x40

    @staticmethod
    def config_user_get (configDict = {}):
        configDict = super(AHF_HeadFixer_PWM_PCA9685, AHF_HeadFixer_PWM_PCA9685).config_user_get (configDict)
        servoAddress = configDict.get ('servoAddress', AHF_HeadFixer_PWM_PCA9685.servoAddressDef)
        userResponse = input('Servo I2C Address, in Hexadecimal, (currently 0x{0x}): '.format (servoAddressDef))
        if userResponse != '':
            servoAddress = int (userResponse, 16)
        configDict.update({'servoAddress' : servoAddress})
        return configDict


    def setup (self):
        super().setup()
        self.pwm = Adafruit_PCA9685.PCA9685 (address=self.configDict.get (servoAddress))
        self.pwm.set_pwm_freq (90) # 40-1000Hz
        self.releaseMouse()


    def set_value (self, servoPosition):
        self.pwm.set_pwm(0, 0, servoPosition)
