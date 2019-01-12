#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_Rewarder_solenoid import AHF_Rewarder_solenoid
import RPi.GPIO as GPIO
from _thread import start_new_thread
from time import sleep

class AHF_Rewarder_solenoid_rpi (AHF_Rewarder_solenoid):
    """
    A class to use a solenoid to deliver water rewards using 1 GPIO pin controlled by RPi.GPIO , using sleep for timing 
    """
    @staticmethod
    def about():
        return 'water rewards by opening a solenoid using 1 GPIO pin, controlled by RPi.GPIO with sleep for timing'

 
    @staticmethod
    def rewardThread (sleepTime, rewardPin):
        GPIO.output(rewardPin, GPIO.HIGH)
        sleep(sleepTime) # not very accurate timing, but good enough
        GPIO.output(rewardPin, GPIO.LOW)

    @staticmethod
    def rewardCMThread (delayTime, sleepTime, rewardPin):
        AHF_Rewarder_solenoid.counterMand = 1
        sleep(delayTime) # not very accurate timing, but good enough
        if AHF_Rewarder_solenoid.counterMand == 1:
            AHF_Rewarder_solenoid.counterMand = 2
            GPIO.output(rewardPin, GPIO.HIGH)
            sleep(sleepTime) # not very accurate timing, but good enough
            GPIO.output(rewardPin, GPIO.LOW)
        

    def setup (self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.cleanup (self.rewardPin)
        GPIO.setup(self.rewardPin, GPIO.OUT)

    def giveReward(self, rewardName):
        """
        Gives a reward of the requested type, if the requested reward type is found in the dictionary

        If the requested reward type is not found, the default reward size is used
        param:rewardName: the tyoe of the reward to be given, should already be in dictionary
        """
        if rewardName in self.rewards:
            sleepTime =self.rewards.get(rewardName)
            start_new_thread (self.rewardThread, (sleepTime,self.rewardPin))
            return sleepTime
        else:
            return 0

    
    def giveRewardCM(self, rewardName):
        if rewardName in self.rewards:
            sleepTime =self.rewards.get(rewardName)
            start_new_thread (self.rewardCMThread, (self.countermandTime, sleepTime,self.rewardPin))
            return sleepTime
        else:
            return 0


    def countermandReward(self):
        if self.countermand == 1:
            self.countermand =0
            return True
        else:
            return False

    def turnON (self):
        GPIO.output(self.rewardPin, GPIO.HIGH)

    def turnOFF (self):
        GPIO.output(self.rewardPin, GPIO.LOW)


            

