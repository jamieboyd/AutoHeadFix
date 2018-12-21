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
    
    #################################Abstract methods subclasses must implement #################################################
    # gets a congiguration dictionary by querying user
    @staticmethod
    @abstractmethod
    def config_user_get ():
        return {}


    @abstractmethod
    def __init__ (self, rewarderDict):
        rewardDict={}

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
    def hardwareTest (self):
        pass


    @abstractmethod
    def turnON (self):
        pass

    @abstractmethod
    def turnOFF (self):
        pass
    

    def editSettings (self):
        """
        Edits settings in the rewarderDict, in a generic way, not having to know ahead of time the name and type of each setting
        """
        AHF_edit_dict (self.rewardDict, 'AHF Rewarder Settings')
        self.setup()    

    def addRewardToDict (self, rewardName, rewardSize):
        self.rewards.update ({rewardName: rewardSize})

#for testing purposes
if __name__ == '__main__':
    import RPi.GPIO as GPIO
    from time import sleep
    from AHF_ClassAndDictUtils import AHF_file_from_user, AHF_class_from_file
    GPIO.setmode (GPIO.BCM)
    rewarderClass = AHF_class_from_file (AHF_file_from_user ('Rewarder', 'AHF Rewarder', '.py'))
    rewarderDict = rewarderClass.config_user_get ()
    rewarder = rewarderClass (rewarderDict)
    print (rewarder.rewardDict)
    print (rewarderClass.rewardUnits)
    total = rewarder.giveReward ("entry")
    print ('Gave entry reward')
    sleep(0.5)
    total += rewarder.giveReward ("task")
    print ('Gave task reward')
    sleep (0.5)
    rewarder.hardwareTest()
    print ('Total rewards given = %f ' % total + rewarderClass.rewardUnits)
    print (rewarder.rewardDict)
    GPIO.cleanup()

