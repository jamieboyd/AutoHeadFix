#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_Rewarder import AHF_Rewarder
import RPi.GPIO as GPIO
from _thread import start_new_thread
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
        rewardPin = int (input('Enter the GPIO pin used by the water delivery solenoid:'))
        rewardDict.update({'rewardPin': rewardPin})
        rewards = {}
        entry = float (input ('Enter solenoid opening duration, in seconds, for entry rewards:'))
        rewards.update({'entry' : entry})
        task = float (input ('Enter solenoid opening duration,in seconds, for task rewards:'))
        rewards.update({'task' : task})
        rewardDict.update({'rewards': rewards})
        return rewardDict

    @staticmethod
    def rewardThread (sleepTime, rewardPin):
        GPIO.output(rewardPin, GPIO.HIGH)
        sleep(sleepTime) # not very accurate timing, but good enough
        GPIO.output(rewardPin, GPIO.LOW)

    def __init__ (self, rewarderDict):
        """
        Makes a new Rewarder object with a GPIO pin and defined opening times for task and entry rewards
        Init inits the dictionary, and setup sets up the GPIO. If we we change GPIO, call setup
        """
        self.rewardDict = rewarderDict
        self.rewards = rewarderDict.get ('rewards')
        if self.rewards is None:
            self.rewards = {'entry':0.1, 'task':0.3}
        else:
            self.rewards.setdefault ('entry', 0.1)
            self.rewards.setdefault ('task', 0.3)
        self.rewardDict.update ({'rewards':self.rewards})
        self.rewardDict.update ({'rewardUnits': 'Seconds'})
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
        if rewardName in self.rewards:
            sleepTime =self.rewards.get(rewardName)
            start_new_thread (AHF_Rewarder_solenoid.rewardThread, (sleepTime,self.rewardPin))
            return sleepTime
        else:
            return 0


    def giveRewardCM(self, rewardName):
        giveReward(self, rewardName)


    def countermandReward(self):
        return 0


    def turnON (self):
        GPIO.output(self.rewardPin, GPIO.HIGH)

    def turnOFF (self):
        GPIO.output(self.rewardPin, GPIO.LOW)

    def hardwareTest (self):
        if not 'hardwareTest' in self.rewards:
            self.addRewardToDict ('hardwareTest', AHF_Rewarder_solenoid.testAmount)
        print ('\nReward Solenoid opening for %f %s' % (AHF_Rewarder_solenoid.testAmount, AHF_Rewarder_solenoid.rewardUnits))
        self.giveReward('hardwareTest')
        inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin (currently ' + str (self.rewardPin) + ')?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.rewardPin = int (input('Enter New Reward Solenoid Pin:' ))
            self.rewardDict.update({'rewardPin': self.rewardPin})
            self.setup()
            

