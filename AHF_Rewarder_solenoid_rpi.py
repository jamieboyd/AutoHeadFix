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
    countermandVal=0
    
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
        AHF_Rewarder_solenoid_rpi.countermandVal = 1
        sleep(delayTime) # not very accurate timing, but good enough
        if AHF_Rewarder_solenoid_rpi.countermandVal== 1:
            AHF_Rewarder_solenoid_rpi.countermandVal = 2
            GPIO.output(rewardPin, GPIO.HIGH)
            sleep(sleepTime) # not very accurate timing, but good enough
            GPIO.output(rewardPin, GPIO.LOW)
            AHF_Rewarder_solenoid_rpi.countermandVal =0 
        

    def setup (self):
        super().setup()
        GPIO.setup(self.rewardPin, GPIO.OUT)
        self.counterMand = 0

    def setdown (self):
        GPIO.cleanup(self.rewardPin)

    def threadReward (self, sleepTime):
        start_new_thread (self.rewardThread, (sleepTime, self.rewardPin))
        
    
    def threadCMReward(self, sleepTime):
        start_new_thread (self.rewardCMThread, (self.countermandTime, sleepTime, self.rewardPin))

    def threadCountermand(self):
        if AHF_Rewarder_solenoid_rpi.countermandVal == 1:
            AHF_Rewarder_solenoid_rpi.countermandVal =0
            return True
        else:
            return False

    def turnON (self):
        GPIO.output(self.rewardPin, GPIO.HIGH)

    def turnOFF (self):
        GPIO.output(self.rewardPin, GPIO.LOW)


            

