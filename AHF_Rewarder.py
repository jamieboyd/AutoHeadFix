#! /usr/bin/python
#-*-coding: utf-8 -*-

from PTCountermandPulse import CountermandPulse
from time import sleep

class AHF_Rewarder:
    """
    A class to use a solenoid to deliver water rewards
    """
    def __init__ (self, defaultTimeVal, rewardPin):
        """
        Makes a new Rewarder object with a GPIO pin and default opening time

        :param defaultTimeVal: opening duration to be used if requested reward Type is not in dictionary
        :param rewardPin: GPIO pin number connected to the solenoid
        :return: returns nothing
        """
        self.rewardPin = rewardPin
        self.gpio_pin, polarity, delay, duration, accuracy_level)
        


    def addToDict(self, rewardName, rewardSize):
        """
        Adds a new reward type with defined size to the dictionary of reward sizes

        param: rewardName: name of new reward type to add
        param:rewardSize: opening duration of solenoid, in seconds        
        """
        self.rewardDict.update({rewardName : rewardSize})
        self.totalsDict.update({rewardName : 0})
        

    def giveReward(self, rewardName):
        """
        Gives a reward of the requested type, if the requested reward type is found in the dictionary

        If the requested reward type is not found, the default reward size is used
        param:rewardName: the tyoe of the reward to be given, should already be in dictionary
        """
        if rewardName in self.rewardDict:
            sleepTime =self.rewardDict.get(rewardName)
        else:
            sleepTime = self.rewardDict.get('default')
        GPIO.output(self.rewardPin, 1)
        sleep(sleepTime) # not very accurate timing, but good enough
        GPIO.output(self.rewardPin, 0)
        self.totalsDict[rewardName] += 1
        return sleepTime

        
#for testing purposes
if __name__ == '__main__':
    rewardPin = 18
    GPIO.setmode (GPIO.BCM)
    rewarder = AHF_Rewarder (30e-03, rewardPin)
    rewarder.addToDict ("entry", 25e-03)
    rewarder.giveReward ("entry")
    sleep(50e-03)
    rewarder.giveReward ("entry")
    sleep(50e-03)
    rewarder.addToDict ("earned", 50e-03)
    rewarder.giveReward ("earned")
    print ('Num entries', rewarder.getNumOfType ("entry"))
    print (rewarder.totalsDict)
    print (rewarder.getTotalDur ())
    GPIO.cleanup()

