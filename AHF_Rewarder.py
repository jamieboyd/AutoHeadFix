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

    def getTotalDur (self):
        """Returns the total duration in seconds of solenoid openings, of all reward types"""
        total = 0
        for key in self.totalsDict.keys():
            total += self.totalsDict[key] * self.rewardDict [key]
        return total

    def getNumOfType (self, rewardName):
        """
        Returns the number of times rewards of a particular reward type have been disbursed

        param:rewardName: the type of the reward queried, should already be in the dictionary, or exception wil be raised
        """
        return self.totalsDict.get(rewardName)

    def setNumOfType (self, rewardName, rewardNum):
        """
        Sets number of rewards of a particular type, if, for example, a rewarder is associated with an existing mouse
        """
        self.totalsDict[rewardName] = rewardNum
        
    def zeroTotals (self):
        """
        Zeros the count of number of rewards given, for all reward types.

        You might want to do this if keeping track of how many rewards have been delivered per day
        """
        for key in self.totalsDict.keys():
            self.totalsDict[key]=0

    def totalsToStr (self):
        """
        Returns a formatted string of total rewards given 

        """
        returnStr = ''
        for key in self.totalsDict.keys():
            if not key == 'default':
                returnStr += str (key) +':' + str (self.totalsDict[key]) + '\t'
        return returnStr
        
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

