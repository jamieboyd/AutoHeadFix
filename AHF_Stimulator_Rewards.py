#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse

from time import time, localtime,timezone, sleep
from datetime import datetime

class AHF_Stimulator_Rewards (AHF_Stimulator):
    
    def __init__ (self, configDict, rewarder, lickDetector,textfp):
        super().__init__(configDict, rewarder, lickDetector, textfp)
        self.setup()

    def setup (self):
        self.nRewards = int (self.configDict.get('nRewards', 5))
        self.rewardInterval = float (self.configDict.get ('rewardInterval', 2.5))
        self.configDict.update({'nRewards' : self.nRewards, 'rewardInterval' : self.rewardInterval})


    @staticmethod
    def dict_from_user (stimDict):
        if not 'nRewards' in stimDict:
            stimDict.update ({'nRewards' : 5})
        if not 'rewardInterval' in stimDict:
            stimDict.update ({'rewardInterval' : 5.0})
        return super(AHF_Stimulator_Rewards, AHF_Stimulator_Rewards).dict_from_user (stimDict)
        
    def run(self):
        timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
        self.rewardTimes = []
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(timeInterval)
        self.mouse.headFixRewards += self.nRewards
        
    def logfile (self):
        event = '\treward'
        mStr = '{:013}'.format(self.mouse.tag) + '\t'
        for rewardTime in self.rewardTimes:
            outPutStr = mStr + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + event
            print (outPutStr)
        if self.textfp != None:
            for rewardTime in self.rewardTimes:
                outPutStr = mStr + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + "\t" + '{:.2f}'.format (rewardTime)  + event
                self.textfp.write(outPutStr + '\n')
            self.textfp.flush()



if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        GPIO.setmode(GPIO.BCM)
        rewarder = AHF_Rewarder (30e-03, 24)
        rewarder.addToDict ('task', 50e-03)
        thisMouse = Mouse (2525, 0,0,0,0)
        #stimFile = AHF_Stimulator.get_stimulator ()
        #stimulator = AHF_Stimulator.get_class (stimFile)(stimdict, rewarder, None)
        stimdict = {'nRewards' : 5, 'rewardInterval' : .25}
        #stimdict = AHF_Stimulator.configure({})
        #print ('stimdict:')
        #for key in sorted (stimdict.keys()):
        #   print (key + ' = ' + str (stimdict[key]))
        stimulator = AHF_Stimulator_Rewards (stimdict, rewarder, None)
        print (stimulator.configStim (thisMouse))
        stimulator.run ()
        stimulator.logfile()
        thisMouse.show()
    except FileNotFoundError:
        print ('File not found')
    finally:
        GPIO.cleanup ()
    

    
