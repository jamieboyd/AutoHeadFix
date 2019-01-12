#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect

class AHF_Rewarder(metaclass = ABCMeta):
    """
    Base class for all rewarder classs. Other rewarders subclass from this, or from one of its subclasses
    """
    rewardUnits = ''
    testAmount = 0
    countermand = 0 # 0 = no reward, or reward countermanded; 1 = waiting for delay; 2 = giving reward, too late to countermand
    defaultCMtime = 2

    
    #################################Abstract methods subclasses must implement #################################################
    @staticmethod
    @abstractmethod
    def about():
        return ''


    # gets a congiguration dictionary by querying user
    @staticmethod
    @abstractmethod
    def config_user_get ():
        return {}

    @abstractmethod
    def __init__ (self, rewardDict):
        self.rewardDict={}

    @abstractmethod
    def setup (self):
        pass

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
    def hardwareTest (self, task):
        pass


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



