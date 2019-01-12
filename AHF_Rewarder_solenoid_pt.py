#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_Rewarder_solenoid import AHF_Rewarder_solenoid
from PTSimpleGPIO import CountermandPulse

class AHF_Rewarder_solenoid_pt (AHF_Rewarder_solenoid):
    """
    A class to use a solenoid to deliver water rewards using 1 GPIO pin, using pulsed thread/PTSimpleGPIO for timing 
    """

    @staticmethod
    def about():
        return 'water rewards by opening a solenoid using 1 GPIO pin, with timing by pulsedThread/PTSimpleGPIO'


    def setup (self):
       self.cmPulse = CountermandPulse (self.rewardPin, 0, 0, self.rewards.get('entry'), 1)


    def giveReward(self, rewardName):
        """
        Gives a reward of the requested type, if the requested reward type is found in the dictionary

        If the requested reward type is not found, the default reward size is used
        param:rewardName: the tyoe of the reward to be given, should already be in dictionary
        """
        if rewardName in self.rewards:
            duration = self.rewards.get (rewardName)
            self.cmPulse.set_delay(0)
            self.cmPulse.set_duration(duration)
            self.cmPulse.do_pulse()
            return duration
        else:
            return 0

    
    def giveRewardCM(self, rewardName):
        if rewardName in self.rewards:
            duration =self.rewards.get(rewardName)
            self.cmPulse.set_duration(duration)
            self.cmPulse.set_delay (self.countermandTime)
            self.cmPulse.do_pulse_countermandable()
            return duration
        else:
            return 0

    def countermandReward(self):
        return cmPulse.countermand_pulse ()

    def turnON (self):
        self.cmPulse.set_level(1,0)

    def turnOFF (self):
        self.cmPulse.set_level(0,0)
