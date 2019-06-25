#! /usr/bin/python
import RPi.GPIO as GPIO
from time import sleep

class AHF_Rewarder:
    """
    A class to use a solenoid to deliver water rewards of various sizes and keep track of rewards delivered.

    A dictionary is used to store different opening durations with user-defined names.
    A separate dictionary with the same keys is used to store the total number of rewards of each
    type that have been delivered. The Rewarder class is inited with a default duration to be used if
    a non-existent key is later requested, and the pin number of the GPIO pin used to
    control the solenoid. Be sure to run GPIO.setmode and GPIO.setup before using the rewarder
    TODO:1)include a measure of flow rate and record/return values in litres delivered, not
    seconds open.2)make doReward threaded, so main program does not have to stop for long reards
    """
    def __init__ (self, defaultTimeVal, rewardPin):
        """
        Makes a new Rewarder object with a GPIO pin and default opening time

        :param defaultTimeVal: opening suration to be used if requested reward Type is not in dictionary
        :param rewardPin: GPIO pin number connected to the solenoid
        :return: returns nothing
        """
        self.rewardDict = {'default': defaultTimeVal}
        self.totalsDict = {'default': 0}
        self.rewardPin = rewardPin
        GPIO.setup (self.rewardPin, GPIO.OUT, initial= GPIO.LOW)


    def addToDict(self, rewardName, rewardSize):
        """
        Adds a new reward type with defined size to the dictionary of reward sizes

        param: rewardName: name of new reward type to add
        param:rewardSize: opening duration of solenoid, in seconds        
        """
        self.rewardDict.update({rewardName : rewardSize})
        

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
        return sleepTime


        
#for testing purposes
if __name__ == '__main__':
    rewardPin = 13
    GPIO.setmode (GPIO.BCM)
    rewarder = AHF_Rewarder (30e-03, rewardPin)
    rewarder.addToDict ("entry", 25e-03)
    rewarder.giveReward ("entry")
    sleep(50e-03)
    rewarder.giveReward ("entry")
    sleep(50e-03)
    rewarder.addToDict ("earned", 50e-03)
    rewarder.giveReward ("earned")
    GPIO.cleanup()

