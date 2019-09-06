#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_Rewarder_solenoid import AHF_Rewarder_solenoid
from PTSimpleGPIO import CountermandPulse

class AHF_Rewarder_solenoid_pt(AHF_Rewarder_solenoid):
    """
    A class to use a solenoid to deliver water rewards using 1 GPIO pin, using pulsed thread/PTSimpleGPIO for timing
    """

    @staticmethod
    def about():
        return 'water rewards by opening a solenoid using 1 GPIO pin, with timing by pulsedThread/PTSimpleGPIO'


    def setup(self):
        super().setup()
        self.cmPulse = CountermandPulse(self.rewardPin, 0, 0, self.rewards.get('entry'), 1)

    def setdown(self):
        del self.cmPulse

    def threadReward(self, sleepTime):
        self.cmPulse.set_delay(0)
        self.cmPulse.set_duration(sleepTime)
        self.cmPulse.do_pulse()


    def threadCMReward(self, sleepTime):
        self.cmPulse.set_duration(sleepTime)
        self.cmPulse.set_delay(self.countermandTime)
        self.cmPulse.do_pulse_countermandable()


    def threadCountermand(self):
        return self.cmPulse.countermand_pulse()

    def turnON(self):
        self.cmPulse.set_level(1,0)

    def turnOFF(self):
        self.cmPulse.set_level(0,0)
