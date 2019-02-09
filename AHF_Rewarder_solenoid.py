#! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Rewarder import AHF_Rewarder
from time import sleep

class AHF_Rewarder_solenoid (AHF_Rewarder,metaclass = ABCMeta):
    """
    An abstract base class to use a solenoid to deliver water rewards using 1 GPIO pin, subclasses use different timing methods
    """
    rewardUnits = 'Seconds'
    testAmount = 1.0
    defaultPin = 13
    defaultEntry = 0.2
    defaultTask = 0.4
    
    @staticmethod
    def config_user_get(starterDict = {}):
        rewardPin = starterDict.get ('rewardPin', AHF_Rewarder_solenoid.defaultPin)
        response = input('Enter the GPIO pin used by the water delivery solenoid (currently %d): ' % rewardPin)
        if response != '':
            rewardPin = int (response)
        rewards = starterDict.get ('rewards', {})
        entry = rewards.get ('entry', AHF_Rewarder_solenoid.defaultEntry)
        response = input ('Enter solenoid opening duration, in seconds, for entry rewards, (currently %.2f): ' % AHF_Rewarder_solenoid.defaultEntry)
        if response != '':
            entry = float (response)
        task = rewards.get ('task', AHF_Rewarder_solenoid.defaultTask)
        response = input ('Enter solenoid opening duration, in seconds, for task rewards, (currently %.2f): ' % AHF_Rewarder_solenoid.defaultTask)
        if response != '':
            task = float (response)
        rewards.update({'entry' : entry, 'task' : task, 'test' : AHF_Rewarder_solenoid.testAmount})
        starterDict.update ({'rewardPin': rewardPin, 'rewards' : rewards})
        return starterDict


    @abstractmethod
    def setup (self):
        self.rewardPin = self.settingsDict.get('rewardPin')
        self.rewards = self.settingsDict.get ('rewards')
        self.countermandTime = self.defaultCMtime

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

    def hardwareTest (self):
        print ('\nReward Solenoid opening for %.2f %s' % (self.testAmount, self.rewardUnits))
        self.giveReward('test')
        sleep (self.testAmount)
        inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin (currently %d)? ' % self.rewardPin)
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.setdown ()
            self.settingsDict = self.config_user_get (self.settingsDict)
            self.setup() 
                    

