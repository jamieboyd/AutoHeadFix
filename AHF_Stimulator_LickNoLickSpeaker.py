#! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
This Stimulator class builds on the LickNoLick class that uses a buzzer and
tries to train mice to not lick until they feel the buzzer.
This class adds a bit of sensory feedback, a piezo speaker that is activated
when they should NOT be licking

A head-fix trial lasts for a set amount of time.
When a trial starts, a cycle begins where the mouse needs to go 2 seconds without registering a lick.
Licking is tested every 0.1 seconds. If the mouse is licking, the speaker plays. If a mouse goes 2sec
without registering a lick, the buzzer buzzes with a series of pulses. No speaker during this time

After a pulsed buzz, the mouse has to wait 0.75 seconds, then has 1 seconds to start licking, after which
a drop of water is delivered. If no licking within the 1 second period, no water is delivered. After water is
delivered, the mouse has 2 seconds to lick without speakr sounding. The cycle then repeats.


The mouse can get as many drops of water as can fit in the trial time. If the mouse does not manage to 
complete a trial correctly, it will get no water in the trial. 

total trial time default = 30 seconds
time they need to go without licking default = 2
time by which buzzer leads reward default = 0.5
GPIO pin for buzzer default = 18
length of each buzz (the ON portion of the train) default = 0.1
time period between start of each buzz ( must be greater than time of each buzz) default = 0.2


GPIO pin for speaker default= 25
speaker frequency default = 300
speaker dutycyle default = 0.8
"""
from PTSimpleGPIO import PTSimpleGPIO, Infinite_train, Train
from AHF_Stimulator_LickNoLick import AHF_Stimulator_LickNoLick
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse
import time
import json
import os
from time import time, sleep
from datetime import datetime
from random import random

class AHF_Stimulator_LickNoLickSpeaker (AHF_Stimulator_LickNoLick):
    speakerPin_def = 25
    speakerFreq_def = 300
    speakerDuty_def = 0.8
    speakerOffForReward_def = 1.5   #time for consuming reward withot getting buzzed at
    buzz_pulseProb_def = 1
    afterStimWitholdTime_def = 0.2
    
    def __init__ (self, configDict, rewarder, lickDetector,textfp):
        super().__init__(configDict, rewarder, lickDetector, textfp)
        self.buzz_pulseProb = float (self.configDict.get ('buzz_pulseProb', AHF_Stimulator_LickNoLickSpeaker.buzz_pulseProb_def))
        self.speakerPin=int(self.configDict.get ('speaker_pin', AHF_Stimulator_LickNoLickSpeaker.speakerPin_def))
        self.speakerFreq=float(self.configDict.get ('speaker_freq', AHF_Stimulator_LickNoLickSpeaker.speakerFreq_def))
        self.speakerDuty = float(self.configDict.get ('speaker_duty', AHF_Stimulator_LickNoLickSpeaker.speakerDuty_def))
        self.speakerOffForReward = float(self.configDict.get ('speaker_OffForReward', AHF_Stimulator_LickNoLickSpeaker.speakerOffForReward_def))
        self.afterStimWitholdTime = float(self.configDict.get ('after_Stim_Withold_Time', AHF_Stimulator_LickNoLickSpeaker.afterStimWitholdTime_def))
        self.speaker=Infinite_train (PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        self.pulseDelay  = self.buzz_period - self.buzz_len
        self.pulseDuration = (self.buzz_period * self.buzz_num) - self.pulseDelay
        # make a second train, we already have self.buzzer for pulsed version, add self.buzzer1 for single pulse version
        self.buzzer1=Train (PTSimpleGPIO.MODE_PULSES, self.buzz_pin, 0, self.pulseDelay, self.pulseDuration, 1,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        self.configDict.update({'speaker_pin' : self.speakerPin, 'speaker_duty' : self.speakerDuty, 'speaker_freq' : self.speakerFreq})
        self.configDict.update({'speaker_OffForReward' : self.speakerOffForReward, 'buzz_pulseProb': self.buzz_pulseProb})
        print ("buzzlead=", self.buzz_lead)

    @staticmethod
    def dict_from_user (stimDict):
        if not 'speaker_pin'in stimDict:
            stimDict.update ({'speaker_pin' : AHF_Stimulator_LickNoLickSpeaker.speakerPin_def})
        if not 'speaker_freq'in stimDict:
            stimDict.update ({'speaker_freq' : AHF_Stimulator_LickNoLickSpeaker.speakerFreq_def})
        if not 'speaker_duty'in stimDict:
            stimDict.update ({'speaker_duty' : AHF_Stimulator_LickNoLickSpeaker.speakerduty_def})
        if not 'speaker_OffForReward'in stimDict:
            stimDict.update ({'speaker_OffForReward' : AHF_Stimulator_LickNoLickSpeaker.speakerOffForReward_def})
        if not 'buzz_pulseProb' in stimDict:
            stimDict.update ({'buzz_pulseProb' : AHF_Stimulator_LickNoLickSpeaker.buzz_pulseProb_def})
        return super(AHF_Stimulator_LickNoLickSpeaker, AHF_Stimulator_LickNoLickSpeaker).dict_from_user (stimDict)


    def run(self):
        """
        every time lickWitholdtime passes with no licks, make a buzz then give a reward after buzz_lead time.
        turn on speaker 
        """
        self.buzzTimes = []
        self.buzzTypes = []
        self.lickWitholdTimes = []
        self.rewardTimes = []
        endTime = time() + self.headFixTime
        speakerIsOn = False
        OffForRewardEnd = 0.0
        # outer loop runs trials until time is up
        while time() < endTime:
            # setup to start a trial, witholding licking for lickWitholdRandom secs till buzzer
            lickWitholdRandom = self.lickWitholdTime + (0.5 - random())
            lickWitholdEnd = time() + lickWitholdRandom
            # inner loop keeps resetting lickWitholdEnd time until  a succsful withhold
            while time() < lickWitholdEnd and time() < endTime:
                anyLicks = self.lickDetector.waitForLick_Soft (0.05)
                if anyLicks == 0:
                    if speakerIsOn == True:
                        self.speaker.stop_train()
                        speakerIsOn = False
                else: # there were licks in witholding period
                    if (speakerIsOn == False) and (time() > OffForRewardEnd):
                        self.speaker.start_train()
                        speakerIsOn = True
                    lickWitholdRandom = self.lickWitholdTime + (0.5 - random())
                    lickWitholdEnd = time() + lickWitholdRandom
            # while loop only exits if trial time is up or lick witholding time passed with no licking
            if anyLicks > 0:
                break
            # at this point, mouse has just witheld licking for lickWitholdTime
            self.lickWitholdTimes.append (lickWitholdRandom)
            # Give a buzz and monitor for no licking in next approx 0.25 secs (afterStimWitholdTime)
            self.buzzTimes.append (time())
            afterBuzzEndTime= time() + self.afterStimWitholdTime
            buzzLeadEnd = afterBuzzEndTime + self.buzz_lead
            if random() < self.buzz_pulseProb: # set up for pulses that get rewarded
                trialType = 2
                self.buzzer1.do_train()
            else:
                trialType = 1
                self.buzzer.do_train()
            # wait for licks - there shouldn't be any for afterStimWitholdTime (approx 0.25 secods) after start of train
            anyLicks = self.lickDetector.waitForLick_Soft (self.afterStimWitholdTime)
            if anyLicks > 0: # licked before 0.75 second after buzzer wait period
                self.speaker.start_train()  # turn on speaker and start over
                speakerIsOn = True
                if trialType == 2:
                    self.buzzTypes.append (-4)
                else:
                    self.buzzTypes.append (-3)
                continue
            else: # animal waited for 0.25 seconds after start of buzzer
                # wait for licks. Animal SHOULD lick for trialType = 2, SHOULD NOT lick for trialType = 1
                anyLicks = self.lickDetector.waitForLick_Soft (self.buzz_lead)
                if trialType == 2: # 
                    if anyLicks > 0: # licked when was supposed to lick
                        if time() < buzzLeadEnd:
                            sleep (buzzLeadEnd - time()) # wait out duration of buzz lead time
                        self.rewardTimes.append (time())
                        self.rewarder.giveReward('task')
                        self.buzzTypes.append (2)
                        OffForRewardEnd = time() + self.speakerOffForReward
                    else: #did not lick when was supposed to lick
                        self.buzzTypes.append (-2)
                else:   # we gave a NO-LICK trial
                    if anyLicks > 0: # licked when was NOT supposed to lick
                        self.buzzTypes.append (-1)
                        self.speaker.start_train()
                        speakerIsOn = True
                    else: # did not lick when was not supposed to lick
                        self.buzzTypes.append (1)
        # make sure to turn off buzzer at end of loop when we exit
        if speakerIsOn == True:
            self.speaker.stop_train()



    def logfile (self):
        
        rewardStr = 'reward'
        buzz2Str = 'Buzz:N=' + str (self.buzz_num) + ',length=' + '{:.2f}'.format(self.buzz_len) + ',period=' + '{:.2f}'.format (self.buzz_period)
        buzz1Str = 'Buzz:N=1,length=' + '{:.2f}'.format (self.pulseDuration) + ',period=' + '{:.2f}'.format (self.pulseDuration + self.pulseDelay)
        mStr = '{:013}'.format(self.mouse.tag)
        iReward =0
        for i in range (0, len (self.buzzTypes)):
            lickWitholdStr = 'lickWitholdTime=' + '{:.2f}'.format (self.lickWitholdTimes [i]) + ','
            if self.buzzTypes [i] == 2: # only rewarded condition
                outPutStr = mStr + '\t' + datetime.fromtimestamp (int (self.rewardTimes [iReward])).isoformat (' ') + '\t' + rewardStr
                print (outPutStr)
                iReward +=1
                buzzStr = buzz2Str  + ',GO=2'
            elif self.buzzTypes [i]==-2:
                buzzStr = buzz2Str  + ',GO=-2'
            elif self.buzzTypes [i] == 1:
                buzzStr = buzz1Str  + ',GO=1'
            elif self.buzzTypes [i] == -1:
                buzzStr = buzz1Str + ',GO=-1'
            elif self.buzzTypes [i] == -3:
                buzzStr = buzz1Str + ',GO=-3'
            elif self.buzzTypes [i] == -4:
                buzzStr = buzz1Str + ',GO=-4'
            
            outPutStr = mStr + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ') + '\t' + lickWitholdStr + buzzStr
            print (outPutStr)
            
        if self.textfp != None:
            iReward =0
            for i in range (0, len (self.buzzTypes)):
                lickWitholdStr = 'lickWitholdTime=' + '{:.2f}'.format (self.lickWitholdTimes [i]) + ','
                if self.buzzTypes [i] == 2: # only rewarded condition
                    outPutStr = mStr + '\t'  + '{:.2f}'.format (self.rewardTimes [iReward]) + '\t'  + rewardStr + '\t' +  datetime.fromtimestamp (int (self.rewardTimes [iReward])).isoformat (' ') + '\n'
                    self.textfp.write(outPutStr)
                    iReward +=1
                    outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + lickWitholdStr + buzz2Str  + ',GO=2'  + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == -2:
                   outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + lickWitholdStr + buzz2Str  + ',GO=-2' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == 1:
                    outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + lickWitholdStr + buzz1Str + ',GO=1' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == -1:
                    outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + lickWitholdStr + buzz1Str + ',GO=-1' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == -3:
                   outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + lickWitholdStr + buzz2Str  + ',GO=-3' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'
                elif self.buzzTypes [i] == -4:
                    outPutStr = mStr + '\t' + '{:.2f}'.format (self.buzzTimes [i]) + '\t' + lickWitholdStr + buzz2Str  + ',GO=-4' + '\t' + datetime.fromtimestamp (int (self.buzzTimes [i])).isoformat (' ')  + '\n'

                self.textfp.write(outPutStr)
            self.textfp.flush()
