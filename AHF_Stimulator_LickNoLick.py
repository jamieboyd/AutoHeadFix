#! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
This Stimulator class uses a buzzer and tries to train mice to not lick until they feel the buzzer
A head-fix trial lasts for a set amount of time
When a trial starts, mouse needs to go 2 seconds without registering a lick, at which time the buzzer
buzzes, and a drop of water is delivered 0.5 seconds later. The cycle then repeats. The mouse
can get as many drops of water as can fit in the trial time. If the mouse does not manage to go
two seconds without licking, it will get no water in the trial

total trial time default = 30 seconds
time they need to go without licking default = 2
time by which buzzer leads reward default = 0.5
GPIO pin for buzzer default = 27
length of each buzz default = 0.1
time period between start of each buzz ( must be greater than time of each buzz) default = 0.2
buzz length/buzz period  = duty cycle
"""
from PTSimpleGPIO import PTSimpleGPIO, Train
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse
import time
import json
import os
from time import time, sleep
from datetime import datetime

class AHF_Stimulator_LickNoLick (AHF_Stimulator):
    headFixTime_def =30
    lickWitholdTime_def = 1
    buzz_pin_def = 27
    buzz_num_def = 2
    buzz_len_def=0.1
    buzz_period_def =0.2
    buzz_lead_def = 1


    def __init__ (self, cageSettings, configDict, rewarder, lickDetector,textfp, camera):
        super().__init__(configDict, rewarder, lickDetector, textfp)
        self.headFixTime = float (self.configDict.get ('headFixTime', AHF_Stimulator_LickNoLick.headFixTime_def))
        self.lickWitholdTime = float (self.configDict.get ('lickWitholdTime', AHF_Stimulator_LickNoLick.lickWitholdTime_def))
        self.buzz_pin = int(self.configDict.get ('buzz_pin', AHF_Stimulator_LickNoLick.buzz_pin_def))
        self.buzz_lead = float (self.configDict.get ('buzz_lead', AHF_Stimulator_LickNoLick.buzz_lead_def))
        self.buzz_num = int (self.configDict.get ('buzz_num', AHF_Stimulator_LickNoLick.buzz_num_def))
        self.buzz_len = float (self.configDict.get ('buzz_len', AHF_Stimulator_LickNoLick.buzz_len_def))
        self.buzz_period = float (self.configDict.get ('buzz_period', AHF_Stimulator_LickNoLick.buzz_period_def))
        print (self.buzz_period, self.buzz_len, self.buzz_num)
        self.buzzer=Train (PTSimpleGPIO.MODE_PULSES, self.buzz_pin, 0, self.buzz_len, (self.buzz_period - self.buzz_len), self.buzz_num,PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        self.configDict.update({'headFixTime' : self.headFixTime, 'lickWitholdTime' : self.lickWitholdTime})
        self.configDict.update({'buzz_pin' : self.buzz_pin, 'buzz_lead' : self.buzz_lead, 'buzz_num' : self.buzz_num})
        self.configDict.update({'buzz_len' : self.buzz_len, "buzz_period" : self.buzz_period})

    @staticmethod
    def dict_from_user (stimDict):
        if not 'headFixTime'in stimDict:
            stimDict.update ({'headFixTime' : AHF_Stimulator_LickNoLick.headFixTime_def})
        if not 'lickWitholdTime'in stimDict:
            stimDict.update ({'lickWitholdTime' : AHF_Stimulator_LickNoLick.lickWitholdTime_def})
        if not 'buzz_pin' in stimDict:
            stimDict.update ({'buzz_pin' : AHF_Stimulator_LickNoLick.buzz_pin_def})
        if not 'buzz_lead' in stimDict:
            stimDict.update ({'buzz_lead' : AHF_Stimulator_LickNoLick.buzz_lead_def})
        if not 'buzz_num' in stimDict:
            stimDict.update ({'buzz_num' : AHF_Stimulator_LickNoLick.buzz_num_def})
        if not 'buzz_len' in stimDict:
            stimDict.update ({'buzz_len' : AHF_Stimulator_LickNoLick.buzz_len_def})
        if not 'buzz_period' in stimDict:
            stimDict.update ({'buzz_period' : AHF_Stimulator_LickNoLick.buzz_period_def})
        return super(AHF_Stimulator_LickNoLick, AHF_Stimulator_LickNoLick).dict_from_user (stimDict)


    def run(self):
        """
        every time lickWitholdtime passes with no licks, make a buzz then give a reward after buzz_lead time.
        """
        self.buzzTimes = []
        self.rewardTimes = []
        endTime = time() + self.headFixTime
        while time() < endTime:
            anyLicks = self.lickDetector.waitForLick_Soft (self.lickWitholdTime, startFromZero=True)
            #print ('Licks = ', anyLicks)
            if anyLicks == 0:
                self.buzzTimes.append (time())
                self.buzzer.do_train()
                sleep (self.buzz_lead)
                self.rewardTimes.append (time())
                self.rewarder.giveReward('task')


    def logfile (self):
        rewardStr = 'reward'
        buzzStr = 'Buzz:N=' + str (self.buzz_num) + ',length=' + '{:.2f}'.format(self.buzz_len) + ',period=' + '{:.2f}'.format(self.buzz_period)
        mStr = '{:013}'.format(self.mouse.tag)
        for i in range (0, len (self.buzzTimes)):
            outPutStr = mStr + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ') + '\t' + buzzStr
            print (outPutStr)
        for i in range (0, len (self.rewardTimes)):
            outPutStr = mStr + '\t' + datetime.fromtimestamp (int (self.rewardTimes [i])).isoformat (' ') + '\t' + rewardStr
            print (outPutStr)
        if self.textfp != None:
            for i in range (0, len (self.buzzTimes)):
                outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + buzzStr + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                self.textfp.write(outPutStr)
            for i in range (0, len (self.rewardTimes)):
                outPutStr = mStr + '\t'  + '{:.2f}'.format (self.rewardTimes [i]) + '\t'  + rewardStr + '\t' +  datetime.fromtimestamp (int (self.rewardTimes [i])).isoformat (' ') + '\n'
                self.textfp.write(outPutStr)
            self.textfp.flush()
