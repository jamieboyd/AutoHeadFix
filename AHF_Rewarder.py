#! /usr/bin/python3
#-*-coding: utf-8 -*-
from time import sleep
from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base

class AHF_Rewarder(AHF_Base, metaclass = ABCMeta):
    """
    Base class for all rewarder classs. Other rewarders subclass from this, or from one of its subclasses
    """
    rewardUnits = ''
    testAmount = 0
    maxEntryRewardsDefault =1000
    maxBreakBeamRewardsDefault = 200
    entryRewardDelayDefault = 1.0


    @abstractmethod
    def giveReward(self, rewardName, resultsDict={}, settingsDict = {}):
        return 0

    @abstractmethod
    def giveRewardCM(self, rewardName, resultsDict={}, settingsDict = {}):
        return 0

    @abstractmethod
    def countermandReward(self,resultsDict={}, settingsDict = {}):
        return 0

    @abstractmethod
    def turnON(self):
        pass

    @abstractmethod
    def turnOFF(self):
        pass

    def addRewardToDict(self, rewardName, rewardSize):
        self.rewards.update({rewardName : rewardSize})


    def setCountermandTime(self, countermandTime):
        self.countermandTime = countermandTime


    def rewardControl(self):
        """
        Opens and closes valve, as for testing, or draining the lines
        """
        try:
            while(True):
                s = input("1 to open, 0 to close, q to quit: ")
                if s == '1':
                    self.turnON()
                    print("Rewarder is ON(open)")
                elif s == '0':
                    self.turnOFF()
                    print("Rewarder is OFF(closed)")
                elif s == 'q':
                    print("RewardControl quitting.")
                    return
                else:
                    print("I understand 1 for open, 0 for close, q for quit.")
        except KeyboardInterrupt:
            print("RewardControl quitting.")


    def hardwareTest(self):
        print('\nReward Solenoid opening for %.2f %s' %(self.testAmount, self.rewardUnits))
        self.giveReward('test')
        sleep(self.testAmount)
        inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin(currently %d)? ' % self.rewardPin)
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.setdown()
            self.settingsDict = self.config_user_get(self.settingsDict)
            self.setup()
        inputStr= input('\nDo you want to run the control program to turn rewarder ON and OFF?(y or n): ')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.rewardControl()
