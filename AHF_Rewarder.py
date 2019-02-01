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
    defaultCMtime = 2


    @abstractmethod
    def giveReward(self, rewardName):
        return 0

    @abstractmethod
    def giveRewardCM(self, rewardName):
        return 0

    @abstractmethod
    def countermandReward(self):
        return 0

    @abstractmethod
    def turnON (self):
        pass

    @abstractmethod
    def turnOFF (self):
        pass

    def addRewardToDict (self, rewardName, rewardSize):
        self.rewards.update ({rewardName : rewardSize})

    def setCountermandTime (self, countermandTime):
        self.countermandTime = countermandTime

    @abstractmethod
    def hardwareTest (self, rewardDict):
        pass



