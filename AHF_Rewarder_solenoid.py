#! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Rewarder import AHF_Rewarder
from time import sleep

class AHF_Rewarder_solenoid (AHF_Rewarder,metaclass = ABCMeta):
    """
    An abstratct base class to use a solenoid to deliver water rewards using 1 GPIO pin, subclasses use different timing methods
    """
    rewardUnits = 'Seconds'
    testAmount = 1
    
    @staticmethod
    def config_user_get():
        rewarderDict={}
        rewardPin = int (input('Enter the GPIO pin used by the water delivery solenoid:'))
        rewarderDict.update({'rewardPin': rewardPin})
        rewards = {}
        entry = float (input ('Enter solenoid opening duration, in seconds, for entry rewards:'))
        rewards.update({'entry' : entry})
        task = float (input ('Enter solenoid opening duration,in seconds, for task rewards:'))
        rewards.update({'task' : task})
        rewarderDict.update ({'rewards' : rewards})
        return rewarderDict


    def __init__ (self, rewarderDict):
        """
        Makes a new Rewarder object with a GPIO pin and defined opening times for task and entry rewards
        Init inits the dictionary, and setup sets up the GPIO. If we we change GPIO, call setup
        """
        self.rewardPin = rewarderDict.get('rewardPin')
        self.rewards = rewarderDict.get ('rewards')
        if self.rewards is None:
            self.rewards = {'entry':0.1, 'task':0.3}
        else:
            self.rewards.setdefault ('entry', 0.1)
            self.rewards.setdefault ('task', 0.3)
        self.rewards.update ({'rewards':self.rewards})
        self.countermandTime = self.defaultCMtime
        self.setup ()

    @abstractmethod
    def setup (self):
        pass

    @abstractmethod
    def giveReward(self, rewardName):
        pass


    @abstractmethod
    def giveRewardCM(self, rewardName):
        pass

    @abstractmethod
    def countermandReward(self):
        pass

    @abstractmethod
    def turnON (self):
        pass

    @abstractmethod
    def turnOFF (self):
        pass

    def hardwareTest (self, rewardDict):
        if not 'hardwareTest' in self.rewards:
           self.addRewardToDict ('hardwareTest', self.testAmount)
        print ('\nReward Solenoid opening for %f %s' % (self.testAmount, self.rewardUnits))
        self.giveReward('hardwareTest')
        sleep (self.testAmount)
        inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin (currently ' + str (self.rewardPin) + ')?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.rewardPin = int (input('Enter New Reward Solenoid Pin:' ))
            rewardDict.update ({'rewardPin': self.rewardPin, 'rewards': self.rewards})
            self.setup()
                    

