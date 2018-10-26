#! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
This Stimulator class builds on the LickNoLick class that uses a buzzer and
tries to train mice to not lick until they feel the buzzer.
This class adds a discrimination task - the mouse is rewarded for a train
of buzzer pulses, but not for a constant buzz of the same duration

A head-fix trial lasts for a set amount of time.
When a trial starts, a cycle begins where the mouse needs to go 2 seconds without registering a lick,
at which time the buzzer buzzes constantly or in a pulsed fashion (50/50 chance of each).

After a pulsed buzz, the mouse has 0.5 seconds to start licking, after which
a drop of water is delivered. If no licking within the 0.5 second period, a 4 second penatlty timeout
is imposed, The cycle then repeats.

After a constant buzz, the mouse has to refrain form licking for 0.5 seconds,
or a penalty timout of 4 seconds is imposed. The cycle then repeats.

The mouse can get as many drops of water as can fit in the trial time. If the mouse does not manage to 
complete a "go" trial correctly, it will get no water in the trial. A two lickport paradigm might be
better here, so mice get rewarded for a correct decision every time, not just half the time.

total trial time default = 30 seconds
time they need to go without licking default = 2
time by which buzzer leads reward default = 0.5
penalty timeout for incorrect choice
GPIO pin for buzzer default = 18
length of each buzz (the ON portion of the train) default = 0.1
time period between start of each buzz ( must be greater than time of each buzz) default = 0.2

buzz length/buzz period  = duty cycle of the train
buzz period - buzz length = OFF poriton of the train
"""
from PTSimpleGPIO import PTSimpleGPIO, Train
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Stimulator_LickNoLick import AHF_Stimulator_LickNoLick
from AHF_Mouse import Mouse
import time
import json
import os
from time import time, sleep
from datetime import datetime
from random import random

class AHF_Stimulator_LickNoLickDisc (AHF_Stimulator_LickNoLick):
    lickWrongTimeout_def = 2
    buzz_pulseProb_def = 0.5
    

    def __init__ (self, configDict, rewarder, lickDetector,textfp):
        super().__init__(configDict, rewarder, lickDetector, textfp)
        self.setup()

    def setup (self):
        super().setup()
        self.lickWrongTimeout = float (self.configDict.get ('lickWrongTimeout', AHF_Stimulator_LickNoLickDisc.lickWrongTimeout_def))
        self.buzz_pulseProb = float (self.configDict.get ('buzz_pulseProb', AHF_Stimulator_LickNoLickDisc.buzz_pulseProb_def))
        self.pulseDelay  = self.buzz_period - self.buzz_len
        print (self.pulseDelay, self.buzz_period, self.buzz_len)
        self.pulseDuration = (self.buzz_period * self.buzz_num) - self.pulseDelay
        # make a second train, we already have self.buzzer for pulsed version, add self.buzzer1 for single pulse version
        self.buzzer1=Train (PTSimpleGPIO.INIT_PULSES, self.pulseDuration, self.pulseDelay, 1, self.buzz_pin, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)

        
    @staticmethod
    def dict_from_user (stimDict):
        if not 'lickWrongTimeout'in stimDict:
            stimDict.update ({'lickWrongTimeout' : AHF_Stimulator_LickNoLickDisc.lickWrongTimeout_def})
        if not 'buzz_pulseProb'in stimDict:
            stimDict.update ({'buzz_pulseProb' : AHF_Stimulator_LickNoLickDisc.buzz_pulseProb_def})
        return super(AHF_Stimulator_LickNoLickDisc, AHF_Stimulator_LickNoLickDisc).dict_from_user (stimDict)


    def run(self):
        """
        every time lickWitholdtime passes with no licks, make a buzz or buzz train, then monitor for licking.
        """
        self.buzzTimes = []
        self.buzzTypes = []
        self.rewardTimes=[]
        endTime = time() + self.headFixTime
        adjustedWitholdTime = self.lickWitholdTime
        while time() < endTime:
            anyLicks = self.lickDetector.waitForLick_Soft (adjustedWitholdTime, startFromZero=True)
            if anyLicks == 0: # successfully waited for withold time
                buzzLeadEnd = time() + self.buzz_lead
                self.buzzTimes.append (time())
                if random() < self.buzz_pulseProb: # set up for pulses that get rewarded
                    self.buzzer1.do_train()
                    anyLicks = self.lickDetector.waitForLick_Soft (self.buzz_lead, startFromZero=True)
                    if anyLicks > 0: # licked when was supposed to lick
                        print ('licked when was supposed to lick')
                        if buzzLeadEnd > time() + 0.05:
                            sleep  (buzzLeadEnd - time())
                        self.rewardTimes.append (time())
                        self.rewarder.giveReward('task')
                        self.buzzTypes.append (2)
                    else: # failed to lick when should have licked
                        print ('failed to lick when should have licked')
                        self.buzzTypes.append (-2)
                        sleep (self.lickWrongTimeout)
                    adjustedWitholdTime = self.lickWitholdTime
                else:   # set up for constant buzz that does NOT get rearded
                    self.buzzer.do_train()
                    anyLicks = self.lickDetector.waitForLick_Soft (self.buzz_lead, startFromZero=True)
                    if anyLicks == 0: #refrained from licking success
                        print ('refrained from licking when supposed to refrain')
                        self.buzzTypes.append (1)
                        adjustedWitholdTime = self.lickWitholdTime - self.buzz_lead # slightly less wait time, that's your reward
                    else:  # licked when should not have licked, time out
                        print ('licked when should not have licked')
                        sleep  (buzzLeadEnd - time() + self.lickWrongTimeout)
                        self.buzzTypes.append (-1)
                        adjustedWitholdTime = self.lickWitholdTime
                        sleep (self.lickWrongTimeout)


    def logfile (self):
        rewardStr = 'reward'
        buzz2Str = 'Buzz:N=' + str (self.buzz_num) + ',length=' + '{:.2f}'.format(self.buzz_len) + ',period=' + '{:.2f}'.format (self.buzz_period)
        buzz1Str = 'Buzz:N=1,length=' + '{:.2f}'.format (self.pulseDuration) + ',period=' + '{:.2f}'.format (self.pulseDuration + self.pulseDelay)
        mStr = '{:013}'.format(self.mouse.tag)
        iReward =0
        for i in range (0, len (self.buzzTypes)):
            if self.buzzTypes [i] == 2: # only rewarded condition
                outPutStr = mStr + '\t' + datetime.fromtimestamp (int (self.rewardTimes [iReward])).isoformat (' ') + '\t' + rewardStr
                print (outPutStr)
                iReward +=1
                buzzStr = buzz2Str + ',GO=2'
            elif self.buzzTypes [i]==-2:
                buzzStr = buzz2Str + ',GO=-2'
            elif self.buzzTypes [i] == 1:
                buzzStr = buzz1Str + ',GO=1'
            elif self.buzzTypes [i] == -1:
                buzzStr = buzz1Str + ',GO=-1'
            outPutStr = mStr + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ') + '\t' + buzzStr
            print (outPutStr)
            
        if self.textfp != None:
            iReward =0
            for i in range (0, len (self.buzzTypes)):
                if self.buzzTypes [i] == 2: # only rewarded condition
                    outPutStr = mStr + '\t'  + '{:.2f}'.format (self.rewardTimes [iReward]) + '\t'  + rewardStr + '\t' +  datetime.fromtimestamp (int (self.rewardTimes [iReward])).isoformat (' ') + '\n'
                    self.textfp.write(outPutStr)
                    iReward +=1
                    outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + buzz2Str + ',GO=2' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == -2:
                   outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + buzz2Str + ',GO=-2' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == 1:
                    outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + buzz1Str + ',GO=1' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == -1:
                    outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + buzz1Str + ',GO=-1' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                self.textfp.write(outPutStr)
            self.textfp.flush()
            
        
