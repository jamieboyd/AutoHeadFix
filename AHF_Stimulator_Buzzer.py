#! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
This Stimulator is subclassed from Rewards. It pulses a buzzer before each reward
We need to know:
GPIO pin for buzzer    default = 18
time by which buzzer leads reward (must be less than time between rewards) default = 0.5
number of buzzes   default = 2
length of each buzz default = 0.1
time period between start of each buzz ( must be greater than time of each buzz) default = 0.2
buzz length/buzz period  = duty cycle
50/50 chance of pulses/single buzz of same length - only reward pulses, not single buzz
"""
from AHF_Stimulator_Rewards import AHF_Stimulator_Rewards
from AHF_LickDetector import AHF_LickDetector
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse
from PTSimpleGPIO import PTSimpleGPIO, Train
from random import random
from array import array
from time import time, localtime,timezone, sleep
from datetime import datetime

class AHF_Stimulator_Buzzer (AHF_Stimulator_Rewards):
    buzz_pin_def = 18
    buzz_lead_def = 0.5
    buzz_num_def = 2
    buzz_len_def=0.1
    buzz_period_def =0.2
    
    def __init__ (self, configDict, rewarder, lickDetector, textfp):
        super().__init__(configDict, rewarder, lickDetector, textfp)
        self.setup()

    def setup (self):
        super().setup() # this sets number of rewards and intervals
        self.buzz_pin = int(self.configDict.get ('buzz_pin', AHF_Stimulator_Buzzer.buzz_pin_def))
        self.buzz_lead = float (self.configDict.get ('buzz_lead', AHF_Stimulator_Buzzer.buzz_lead_def))
        self.buzz_num = int (self.configDict.get ('buzz_num', AHF_Stimulator_Buzzer.buzz_num_def))
        self.buzz_len = float (self.configDict.get ('buzz_len', AHF_Stimulator_Buzzer.buzz_len_def))
        self.buzz_period = float (self.configDict.get ('buzz_period', AHF_Stimulator_Buzzer.buzz_period_def))
        self.buzzer=Train (PTSimpleGPIO.INIT_PULSES, self.buzz_len, (self.buzz_period  - self.buzz_len), self.buzz_num, self.buzz_pin, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        self.configDict.update({'buzz_pin' : self.buzz_pin, 'buzz_lead' : self.buzz_lead, 'buzz_num' : self.buzz_num})
        self.configDict.update({'buzz_len' : self.buzz_len, "buzz_period" : self.buzz_period})

    @staticmethod
    def dict_from_user (stimDict):
        if not 'buzz_pin' in stimDict:
            stimDict.update ({'buzz_pin' : AHF_Stimulator_Buzzer.buzz_pin_def})
        if not 'buzz_lead' in stimDict:
            stimDict.update ({'buzz_lead' : AHF_Stimulator_Buzzer.buzz_lead_def})
        if not 'buzz_num' in stimDict:
            stimDict.update ({'buzz_num' : AHF_Stimulator_Buzzer.buzz_num_def})
        if not 'buzz_len' in stimDict:
            stimDict.update ({'buzz_len' : AHF_Stimulator_Buzzer.buzz_len_def})
        if not 'buzz_period' in stimDict:
            stimDict.update ({'buzz_period' : AHF_Stimulator_Buzzer.buzz_period_def})
        return super(AHF_Stimulator_Buzzer, AHF_Stimulator_Buzzer).dict_from_user (stimDict)


    def configStim (self, mouse):
        self.timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
        doPulses = array ('i', (round(random ())  for i in range (0, self.nRewards))) # 50% chance of 1 or 0
        self.rewardTimes = []
        self.buzzTimes=[]
        stimStr = 'stim'
        for value in doPulses:
            stimStr += str (value)
        return stimStr
        
    def run(self):
        """
        do a buzz sleep for lead time - buzz time. give a reward. sleep for reward interval - reward time - buzz lead time
        """
        #buzzTime = self.buzz_period * self.buzz_num
        #buzzInterSleep = self.buzz_period - self.buzz_len
        #buzzLeadSleep = self.buzz_lead - buzzTime
        
        for reward in range(self.nRewards):
            self.buzzTimes.append (time())
            self.buzzer.do_train()
            sleep (buzzLeadSleep)
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(timeInterval)
        self.mouse.headFixRewards += self.nRewards
        
        
    def logfile (self):
        super().logfile ()
        event = '\tBuzz:N=' + str (self.buzz_num) + 'length=' + str (self.buzz_len) + ',period=' + str (self.buzz_period)
        mStr = '{:013}'.format(self.mouse.tag) + '\t'
        for buzzTime in self.buzzTimes:
            outPutStr = mStr + datetime.fromtimestamp (int (buzzTime)).isoformat (' ') + event
            print (outPutStr)
        if self.textfp != None:
            for buzzTime in self.buzzTimes:
                outPutStr = mStr + datetime.fromtimestamp (int (buzzTime)).isoformat (' ') + "\t" + '{:.2f}'.format (buzzTime)  + event
                self.textfp.write(outPutStr + '\n')
            self.textfp.flush()



if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        #GPIO.setmode(GPIO.BCM)
        rewarder = AHF_Rewarder (30e-03, 24)
        rewarder.addToDict ('task', 50e-03)
        thisMouse = Mouse (2525, 0,0,0,0)
        #stimFile = AHF_Stimulator.get_stimulator ()
        #stimulator = AHF_Stimulator.get_class (stimFile)(stimdict, rewarder, None)
        stimdict = {'nRewards' : 5, 'rewardInterval' : 3, 'buzz_pin' : AHF_Stimulator_Buzzer.buzz_pin_def, 'buzz_num': AHF_Stimulator_Buzzer.buzz_num_def}
        stimdict.update ({'buzz_lead' : AHF_Stimulator_Buzzer.buzz_lead_def, 'buzz_len' : AHF_Stimulator_Buzzer.buzz_len_def, 'buzz_period' : AHF_Stimulator_Buzzer.buzz_period_def})
        #stimdict = AHF_Stimulator.configure({})
        #print ('stimdict:')
        #for key in sorted (stimdict.keys()):
        #   print (key + ' = ' + str (stimdict[key]))
        stimulator = AHF_Stimulator_Buzzer (stimdict, rewarder, None)
        print (stimulator.configStim (thisMouse))
        stimulator.run ()
        stimulator.logfile()
        thisMouse.show()
    except FileNotFoundError:
        print ('File not found')
    finally:
        GPIO.cleanup ()
    

    
