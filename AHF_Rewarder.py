#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base

class AHF_Rewarder(AHF_Base, metaclass = ABCMeta):
    """
    Base class for all rewarder classs. Other rewarders subclass from this, or from one of its subclasses
    """
    rewardUnits = ''
    testAmount = 0
    defaultMaxEntryRewards =1000
    defaultEntryRewardDelay = 1.0

    @staticmethod
    @abstractmethod
    def config_user_get (starterDict = {}):
        """
        static method that querries user for settings, with default responses from starterDict,
        and returns starterDict with settings as edited by the user.

        """
        maxEntryRewards = starterDict.get ('maxEntryRewards', AHF_Rewarder.defaultMaxEntryRewards)
        response = input('Enter the maximum number of entry reards given per day (currently %d): ' % maxEntryRewards)
        if response != '':
            maxEntryRewards = int (response)
        entryRewardDelay = starterDict.get ('entryRewardDelay', AHF_Rewarder.defaultEntryRewardDelay)
        response = input('Enter the delay between entering and getting a reward (currently %.2f): ' % defaultEntryRewardDelay)
        if response != '':
            entryRewardDelay = float (response)
        starterDict.update ({'maxEntryRewards' : maxEntryRewards, 'entryRewardDelay' : entryRewardDelay})
        return starterDict

            
    @abstractmethod
    def giveReward(self, rewardName, resultDict):
        return 0

    @abstractmethod
    def giveRewardCM(self, rewardName, resultDict):
        return 0

    @abstractmethod
    def countermandReward(self, resultDict):
        return 0

    @abstractmethod
    def turnON (self):
        pass

    @abstractmethod
    def turnOFF (self):
        pass

    def addRewardToDict (self, rewardName, rewardSize):
        self.rewards.update ({rewardName : rewardSize})


    def config_user_addDictToMouse (self, mouse):
        if hasattr (mouse, 'RewarderDict'):
             mouse.RewarderDict = self.config_user_get(starterDict = mouse.RewarderDict)
        else:
            setattr (mouse, 'RewarderDict', self.config_user_get(starterDict = self.settingsDict))
            

    def setCountermandTime (self, countermandTime):
        self.countermandTime = countermandTime

    @abstractmethod
    def hardwareTest (self):
        pass
        
    def rewardControl (self):
        """
        Opens and closes valve, as for testing, or draining the lines

        when run as a module, valveControl assumes GPIO is setup as defined in cageSet and offers to open/close water
        delivery solenoid. ValveControl takes an instance of AHF_CageSet as a paramater and assumes
        that the GPIO pin connected to the water delivery solenoid us as defined in the cageSet, and
        that GPIO is already setup.
        param:cageSet: an instance of AHF_CageSet describing which pin is used for water reward solenoid
        returns:nothing
        """
        try:
            while (True):
                s = input("1 to open, 0 to close, q to quit: ")
                if s == '1':
                    self.turnON ()
                    print ("Rewarder is ON (open)")
                elif s == '0':
                    self.turnOFF ()
                    print ("Rewarder is OFF (closed)")
                elif s == 'q':
                    print ("RewardControl quitting.")
                    break
                else:
                    print ("I understand 1 for open, 0 for close, q for quit.")
        except KeyboardInterrupt:
            print ("RewardControl quitting.")
            



