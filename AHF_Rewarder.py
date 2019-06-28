#! /usr/bin/python
import RPi.GPIO as GPIO
from time import sleep
from _thread import start_new_thread

class AHF_Rewarder:
    """
    A class to use a solenoid to deliver water rewards of various sizes and keep track of rewards delivered.

    A dictionary is used to store different opening durations with user-defined names.
    The Rewarder class is inited with a default duration to be used if
    a non-existent key is later requested, and the pin number of the GPIO pin used to
    control the solenoid. Be sure to run GPIO.setmode (GPIO.BCM) before initing the rewarder
    TODO:1)include a measure of flow rate and record/return values in litres delivered, not
    seconds open. 2) make doReward threaded, so main program does not have to stop for long rewards (done)
    """
    countermandVal = 0 # class variabe used for countermanding rewards after a delay
    
    @staticmethod
    def rewardThread (sleepTime, rewardPin):
        """
        funtion to run in a thread to give a water reward
        :param sleepTime: duration in seconds to sleep while solenoid is open
        :param rewardPin: number of GPIO pin connected to solenoid
        """
        GPIO.output(rewardPin, GPIO.HIGH)
        sleep(sleepTime) # not very accurate timing, but good enough
        GPIO.output(rewardPin, GPIO.LOW)
        
    @staticmethod
    def rewardCMThread (delayTime, sleepTime, rewardPin):
        """
        funtion to run in a thread to give a water reward, with a delay before reweard is given
        during delay period, reward can be countermanded
        :param delayTime: period before reward is given, wherin reward can be countermanded 
        :param sleepTime: duration in seconds to sleep while solenoid is open
        :param rewardPin: number of GPIO pin connected to solenoid
        """
        AHF_Rewarder.countermandVal = 1 # indicate we are in delay period where reward can be countermanded
        sleep(delayTime) # not very accurate timing, but good enough
        if AHF_Rewarder.countermandVal == 1: # reward was not countermanded, so give reward
            AHF_Rewarder.countermandVal = 2 # indicate that reward was given
            GPIO.output(rewardPin, GPIO.HIGH)
            sleep(sleepTime) # not very accurate timing, but good enough
            GPIO.output(rewardPin, GPIO.LOW)            
            
    def __init__ (self, defaultTimeVal, rewardPin):
        """
        Makes a new Rewarder object with a GPIO pin and default opening time

        :param defaultTimeVal: opening suration to be used if requested reward Type is not in dictionary
        :param rewardPin: GPIO pin number connected to the solenoid
        :return: returns nothing
        """
        self.rewardDict = {'default': defaultTimeVal}
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
        param:rewardName: the type of the reward to be given, should already be in dictionary
        """
        
        if rewardName in self.rewardDict:
            sleepTime = self.rewardDict.get(rewardName)
        else:
            sleepTime = self.rewardDict.get('default')
        start_new_thread (AHF_Rewarder.rewardThread, (sleepTime, self.rewardPin))

    def giveRewardCM(self, rewardName, delayTime):
        """
        Gives a reweard after a delay period, during delay period reward can be countermanded
        
        :param rewardName: the type of the reward to be given, should already be in dictionary
        :param delayTime: delay time during which reward can be countermanded
        """
        if rewardName in self.rewardDict:
            sleepTime = self.rewardDict.get(rewardName)
        else:
            sleepTime = self.rewardDict.get('default')
        start_new_thread (AHF_Rewarder.rewardCMThread, (delayTime, sleepTime, self.rewardPin))
    
    
    def countermandReward(self):
        """
        countermands reward by setting class variable to 0
        :returns: truth that the reward was countermanded, i.e. False if reward was already given
        """
        if AHF_Rewarder.countermandVal == 2:
            AHF_Rewarder.countermandVal = 0
            return False
        else:
            AHF_Rewarder.countermandVal = 0
            return True
    
    
#for testing purposes
if __name__ == '__main__':
    rewardPin = 13
    GPIO.setmode (GPIO.BCM)
    GPIO.setwarnings (False)
    rewarder = AHF_Rewarder (30e-03, rewardPin)
    rewarder.addToDict ("entry", 100e-03)
    rewarder.giveReward ("entry")
    sleep(1)
    rewarder.addToDict ("earned", 150e-03)
    rewarder.giveReward ("earned")
    sleep(1)
    rewarder.giveRewardCM ("entry", 2)
    sleep (0.5)
    print (rewarder.countermandReward ())
    sleep (1)
    GPIO.cleanup()

