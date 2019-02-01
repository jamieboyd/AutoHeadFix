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
    defaultAddress = 0x40
    @staticmethod
    def about():
        return 'PCA9685 servo driver over i2c controls a servo motor to push head bar'


    @staticmethod
    def config_user_get (starterDict = {}):
        starterDict.update (AHF_HeadFixer_PWM.config_user_get(starterDict))
        servoAddress = starterDict.get ('servoAddress', AHF_HeadFixer_PWM_PCA9685.defaultAddress)
        response = input("Enter Servo I2C Address, in Hexadecimal, currently 0x%x: " % servoAddress)
        if response != '':
            servoAddress = int (response, 16)
        starterDict.update ({'servoAddress' : servoAddress})
        return starterDict


    def setup (self):
        super().setup()
        self.servoAddress = self.settingsDict.get ('servoAddress')
        self.PCA9685 = Adafruit_PCA9685.PCA9685 (address=self.servoAddress)
        self.PCA9685.set_pwm_freq (90) # 40-1000Hz
        self.setPWM (self.servoReleasedPosition)

    def setdown (self):
        del self.PCA9685

    def setPWM (self, servoPosition):
        self.PCA9685.set_pwm(0, 0, servoPosition)
        
    
