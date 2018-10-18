#! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
sudo apt-get install i2c-tools
sudo apt-get install python3-smbus
git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
git clone https://github.com/adafruit/Adafruit_Python_PCA9685.git


"""

# Import the PCA9685 module.
import Adafruit_PCA9685
from AHF_HeadFixer import AHF_HeadFixer
import AHF_CageSet
from time import sleep
class AHF_HeadFixer_ServoDriver (AHF_HeadFixer):

    def __init__(self, cageSet):
        self.hasLevels = True
        self.pwm = Adafruit_PCA9685.PCA9685 (address=cageSet.servoAddress)
        self.servoReleasedPosition = cageSet.servoReleasedPosition
        self.servoFixedPosition = cageSet.servoFixedPosition # maximum tight fixed position
        self.servoPosition = cageSet.servoFixedPosition
        self.levelIncrement = cageSet.servoLevelIncrement
        self.levelStart = cageSet.servoLevelStart
        self.pwm.set_pwm_freq (90) # 40-1000Hz
        self.releaseMouse()

    def fixMouse(self):
        self.pwm.set_pwm(0, 0, self.servoPosition)

    def releaseMouse(self):
        self.pwm.set_pwm(0, 0, self.servoReleasedPosition)
        
    @staticmethod
    def configDict_read (cageSet, configDict):
        cageSet.servoAddress = int(configDict.get('Servo Address', 0x40))
        cageSet.servoReleasedPosition = int(configDict.get('Released Servo Position', 815))
        cageSet.servoFixedPosition = int(configDict.get('Fixed Servo Position', 500))
        cageSet.servoLevelStart = int(configDict.get('Fixed Servo Position', 500))
        cageSet.servoLevelIncrement = int(configDict.get('Servo level Increment', 50))
    
    @staticmethod
    def configDict_set(cageSet,configDict):
        configDict.update ({'Servo Address':cageSet.servoAddress, 'Released Servo Position':cageSet.servoReleasedPosition,'Fixed Servo Position':cageSet.servoFixedPosition})

    @staticmethod
    def config_user_get (cageSet):
        cageSet.servoAddress = int(input("Servo I2C Address, in Hexadecimal, default is 0x40): "), 16)
        cageSet.servoReleasedPosition = int(input("Servo Released Position (0-4095): "))
        cageSet.servoFixedPosition = int(input("Servo Fixed Position (0-4095): "))

    @staticmethod
    def config_show(cageSet):
        return 'ServoDriver I2C Address, in Hexadecimal, default is 0x40 =' + str(cageSet.servoAddress) + '\n\tReleased Servo Position=' + str(cageSet.servoReleasedPosition) + '\n\tFixed Servo Position=' + str(cageSet.servoFixedPosition)
        

    def test (self, cageSet):
        print ('ServoDriver moving to Head-Fixed position for 2 seconds')
        self.fixMouse()
        sleep (2)
        self.releaseMouse()
        print ('ServoDriver moving to Released position')
        inputStr= input('Do you want to change fixed position, currently ' + str (cageSet.servoFixedPosition) + ', or released position, currently ' + str(cageSet.servoReleasedPosition) + ':')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            cageSet.servoFixedPosition = int (input('Enter New Servo Fixed Position:'))
            cageSet.servoReleasedPosition = int (input('Enter New Servo Released Position:'))
            self.servoReleasedPosition = cageSet.servoReleasedPosition
            self.servoFixedPosition = cageSet.servoFixedPosition


        
        
if __name__ == "__main__":
    from time import sleep
    hardWare = AHF_CageSet ()
    hardWare.edit()
    hardWare.save()
    s = AHF_HeadFixer_ServoDriver(hardWare)
    s.fixMouse()
    sleep(5)
    s.releaseMouse()
