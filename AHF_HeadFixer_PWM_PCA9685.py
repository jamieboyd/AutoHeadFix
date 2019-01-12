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
    """
    inherits from AHF_HeadFixer_PWM
    """

    @staticmethod
    def about():
        return 'PCA9685 servo driver over i2c controls a servo motor to push head bar'
    
    def __init__(self, headFixerDict):
        super().__init__(headFixerDict)
        self.servoAddress = headFixerDict.get('servoAddress')

    def setup (self):
        self.PCA9685 = Adafruit_PCA9685.PCA9685 (address=self.servoAddress)
        self.PCA9685.set_pwm_freq (90) # 40-1000Hz
        self.setPWM (self.servoReleasedPosition)

    def setPWM (self, servoPosition):
        self.PCA9685.set_pwm(0, 0, servoPosition)
        
    @staticmethod
    def config_user_get ():
        headFixDict = super(AHF_HeadFixer_PWM_PCA9685, AHF_HeadFixer_PWM_PCA9685).config_user_get ()
        userResponse = input("Servo I2C Address, in Hexadecimal, or enter for default 0x40: ")
        if userResponse == '':
            userResponse = '0x40'
        userResponse = int (userResponse, 16)
        headFixDict.update ({'servoAddress' : userResponse})
        return headFixDict
