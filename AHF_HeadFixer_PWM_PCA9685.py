#! /usr/bin/python3
#-*-coding: utf-8 -*-
"""
Controls a PCA9685 servo driver IC
Requires Adafruit_PCA9685 library, which can be obtained from github
git clone https://github.com/adafruit/Adafruit_Python_PCA9685
cd Adafruit_Python_PCA9685
sudo python3 setup.py install
"""

from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM # abstract base class for servo-driver headfixers using PWM
import Adafruit_PCA9685 # the PCA9685 module drives the external PCA9685 servo driver IC on the i2c bus

class AHF_HeadFixer_PWM_PCA9685 (AHF_HeadFixer_PWM):
    """
    Controls a PCA9685 servo driver IC using Adafruit_PCA9685 library
    """
    servoAddressDef = 0x40

    @staticmethod
    def about ():
        """
        :returns: a string describing function of PCA9685 headFixer
        """
        return 'Controls a servo motor using external PCA9685 servo driver IC on the i2c bus' 

    @staticmethod
    def config_user_get (configDict = {}):
        """
        querries user to geta  dictionary of settings for i2c address and PWM settings
        :param configDict: starter dictionary to fillout with setings
        :returns: the same dictionary, filled in or edited
        """
        configDict = super(AHF_HeadFixer_PWM_PCA9685, AHF_HeadFixer_PWM_PCA9685).config_user_get (configDict)
        servoAddress = configDict.get ('servoAddress', AHF_HeadFixer_PWM_PCA9685.servoAddressDef)
        userResponse = input('Servo I2C Address, in Hexadecimal, (currently 0x{:0x}): '.format (servoAddress))
        if userResponse != '':
            servoAddress = int (userResponse, 16)
        configDict.update({'servoAddress' : servoAddress})
        return configDict


    def setup (self):
        """
        sets up i2c communication with PCA9685 ic
        """
        super().setup()
        self.pwm = Adafruit_PCA9685.PCA9685 (address=self.configDict.get ('servoAddress'))
        self.pwm.set_pwm_freq (90) # 40-1000Hz
        self.releaseMouse()


    def set_value (self, servoPosition):
        """
        sets the PCA9685 to output the requested value
        """
        self.pwm.set_pwm(0, 0, servoPosition)
