#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_Rewarder import AHF_Rewarder
import RPi.GPIO as GPIO
from time import sleep

class AHF_Rewarder_solenoid (AHF_Rewarder):
    """
    A class to use a solenoid to deliver water rewards using 1 GPIO pin using sleep for timing 
    """
    rewardUnits = 'Seconds'
    testAmount = 1
    @staticmethod
    def config_user_get ():
        rewardDict={}
        entrance = float (input ('Enter solenoid opening duration, in seconds, for entrance rewards:'))
        rewardDict.update({'entrance' : entrance})
        task = float (input ('Enter solenoid opening duration,in seconds, for task rewards:'))
        rewardDict.update({'task' : task})
        rewardPin = int (input('Enter the GPIO pin used by the water delivery solenoid:'))
        rewardDict.update({'rewardPin': rewardPin})
        return rewardDict

        
    def __init__ (self, rewarderDict):
        """
        Makes a new Rewarder object with a GPIO pin and defined opening times for task and entry rewards
        """
        self.rewardDict = rewarderDict
        self.rewardDict.update ({'rewardUnits': 'Seconds'})
        self.rewardDict.update ({'test': AHF_Rewarder_solenoid.testAmount})
        self.rewardDict.update({'entrance': self.rewardDict.get('entrance', 0.1)})
        self.rewardDict.update({'task': self.rewardDict.get('task', 0.3)})
        self.rewardPin =0
        self.setup ()


    def setup (self):
        if self.rewardPin != 0:
            GPIO.cleanup (self.rewardPin)
        self.rewardPin = self.rewardDict.get('rewardPin')
        GPIO.setup(self.rewardPin, GPIO.OUT)
        

    def giveReward(self, rewardName):
        """
        Gives a reward of the requested type, if the requested reward type is found in the dictionary

        If the requested reward type is not found, the default reward size is used
        param:rewardName: the tyoe of the reward to be given, should already be in dictionary
        """
        if rewardName in self.rewardDict:
            sleepTime =self.rewardDict.get(rewardName)
            GPIO.output(self.rewardPin, GPIO.HIGH)
            sleep(sleepTime) # not very accurate timing, but good enough
            GPIO.output(self.rewardPin, GPIO.LOW)
            return sleepTime
        else:
            return 0


    def giveRewardCM(self, rewardName):
        giveReward(self, rewardName)


    def countermandReward(self):
        return 0


    def hardwareTest (self):
        print ('\nReward Solenoid opening for %f %s' % self.rewardDict.get ('test'), AHF_Rewarder_solenoid.rewardUnits)
        inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin (currently ' + str (self.rewardPin) + ')?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.rewardPin = int (input('Enter New Reward Solenoid Pin:' ))
            self.rewardDict.update({'rewardPin': task.rewardPin})
            self.setup()
            

