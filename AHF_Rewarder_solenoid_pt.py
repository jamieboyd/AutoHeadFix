#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_Rewarder import AHF_Rewarder
from PTSimpleGPIO import CountermandPulse

class AHF_Rewarder_solenoid_pt (AHF_Rewarder):
    """
    A class to use a solenoid to deliver water rewards using 1 GPIO pin, using sleep for timing 
    """
    rewardUnits = 'Seconds'
    testAmount = 1
    counterMand = 0 # 0 no reward, or reward countermanded; 1 waiting for delay; 2 giving reward
    defaultCMtime = 2
    @staticmethod
    def config_user_get ():
        rewardDict={}
        rewardPin = int (input('Enter the GPIO pin used by the water delivery solenoid:'))
        rewardDict.update({'rewardPin': rewardPin})
        rewards = {}
        entry = float (input ('Enter solenoid opening duration, in seconds, for entry rewards:'))
        rewards.update({'entry' : entry})
        task = float (input ('Enter solenoid opening duration,in seconds, for task rewards:'))
        rewards.update({'task' : task})
        rewardDict.update({'rewards': rewards})
        return rewardDict

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
        

    def __init__ (self, rewarderDict):
        """
        Makes a new Rewarder object with a GPIO pin and defined opening times for task and entry rewards
        Init inits the dictionary, and setup sets up the GPIO. If we we change GPIO, call setup
        """
        self.rewardDict = rewarderDict
        self.rewards = rewarderDict.get ('rewards')
        if self.rewards is None:
            self.rewards = {'entry':0.1, 'task':0.3}
        else:
            self.rewards.setdefault ('entry', 0.1)
            self.rewards.setdefault ('task', 0.3)
        self.rewardDict.update ({'rewards':self.rewards})
        self.rewardDict.update ({'rewardUnits': 'Seconds'})
        self.rewardDict.update ({'test': AHF_Rewarder_solenoid.testAmount})
        self.rewardDict.update({'entrance': self.rewardDict.get('entrance', 0.1)})
        self.rewardDict.update({'task': self.rewardDict.get('task', 0.3)})
        self.countermandTime = defaultCMtime
        self.rewardPin =0
        self.setup ()

    def setup (self):
        if self.rewardPin != 0:
            GPIO.cleanup (self.rewardPin)
        self.rewardPin = self.rewardDict.get('rewardPin')
        GPIO.setup(self.rewardPin, GPIO.OUT)

    def giveReward(self, rewardName):
        """
        Gives a reward of the requested type, if the requested reward type is found in the dictionary

        If the requested reward type is not found, the default reward size is used
        param:rewardName: the tyoe of the reward to be given, should already be in dictionary
        """
        if rewardName in self.rewards:
            sleepTime =self.rewards.get(rewardName)
            start_new_thread (AHF_Rewarder_solenoid.rewardThread, (sleepTime,self.rewardPin))
            return sleepTime
        else:
            return 0


    def setCountermandTime (self):
        self.countermandTime = defaultCMtime
    
    def giveRewardCM(self, rewardName):
        if rewardName in self.rewards:
            sleepTime =self.rewards.get(rewardName)
            start_new_thread (AHF_Rewarder_solenoid.rewardCMThread, (self.countermandTime, sleepTime,self.rewardPin))
            return sleepTime
        else:
            return 0


    def countermandReward(self):
        if AHF_Rewarder_solenoid.counterMand == 1:
            AHF_Rewarder_solenoid.counterMand =0
            return True
        else:
            return False

    def turnON (self):
        GPIO.output(self.rewardPin, GPIO.HIGH)

    def turnOFF (self):
        GPIO.output(self.rewardPin, GPIO.LOW)

    def hardwareTest (self):
        if not 'hardwareTest' in self.rewards:
            self.addRewardToDict ('hardwareTest', AHF_Rewarder_solenoid.testAmount)
        print ('\nReward Solenoid opening for %f %s' % (AHF_Rewarder_solenoid.testAmount, AHF_Rewarder_solenoid.rewardUnits))
        self.giveReward('hardwareTest')
        inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin (currently ' + str (self.rewardPin) + ')?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.rewardPin = int (input('Enter New Reward Solenoid Pin:' ))
            self.rewardDict.update({'rewardPin': self.rewardPin})
            self.setup()
            

