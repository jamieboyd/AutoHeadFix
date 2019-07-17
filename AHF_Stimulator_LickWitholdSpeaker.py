#! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
This Stimulator class uses a lick detector, a vibration motor buzzer and a piezo speaker
to train mice to not lick until they feel the buzzer. This class adds a bit of sensory feedback,
a piezo speaker that is activated when they should NOT be licking

A head-fix session lasts for a set amount of time. When a session starts, a cycle begins where the mouse needs to go
lickWitholdTime seconds without registering a lick. Licking is tested every 0.1 seconds. If the mouse is licking,
the speaker plays. If a mouse goes lickWitholdTime seconds without registering a lick, the vibe motor buzzer buzzes with a series of pulses.

After the vibe motor, the mouse has to wait afterBuzz_withold seconds (which can be zero) before licking, or the trial is over code -4
After afterBuzz_withold, the mouse has lick_window seconds to start licking. If no licks are registered, the trial is over code -2
If a lick is registwered in  lick_window, drop of water is delivered. the trial is over with code 2
If no licking within the lick_window period, no water is delivered. After water is delivered, the mouse has speakerOffForReward seconds
to lick without the speaker sounding. 

The mouse can get as many drops of water as can fit in the session time. If the mouse does not manage to 
complete a trial correctly, it will get no water in the session. 


"""
from PTSimpleGPIO import PTSimpleGPIO, Infinite_train, Train
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse, Mice
import time
import json
import os
from time import time, sleep
from datetime import datetime
from random import random

class AHF_Stimulator_LickWitholdSpeaker (AHF_Stimulator):
    """
     Stimulatopr class that trains a mouse, using auditory feedback, to withold from licking the reward spout until tactile feedback from a vibe motor buzzer.'

    """
    headFixTime_def =30
    lickWitholdTime_def = 1
    randomize_withold_def = False
    afterBuzz_withold_def = 0 # i.e.. mouse does not have have to refrain form licking after the buzzer sounds
    lick_window_def = 0 # i,e, mouse does not have to lick within a time window to get a reward
    
    buzz_pin_def = 27
    buzz1_num_def = 2
    buzz1_len_def=0.1
    buzz1_period_def =0.2

    speakerPin_def = 25
    speakerFreq_def = 300
    speakerDuty_def = 0.8 # this is pretty much always 0.8, so it does not need to go in setup dictionary
    speakerOffForReward_def = 1.5   #time for consuming reward without getting buzzed at


    @staticmethod
    def about ():
        """
        returns:a brief description of the LickWitholdStimulator class
        """
        return 'Trains a mouse, using auditory feedback, to withold from licking the reward spout until getting tactile feedback from a vibe motor buzzer'


    @staticmethod
    def dict_from_user (stimDict = {}):
        """
        querries user to edit and return a dictionary of settings for LickWitholdSpeaker stimulator
        """
        # *************** task/performance metrics *****************
        # head fix duration
        headFixTime = stimDict.get('headFixTime', AHF_Stimulator_LickWitholdSpeaker.headFixTime_def)
        tempInput = input ('set duration of each head fix session (currently {:.1f}) to:'.format (headFixTime))
        if tempInput != '':
            headFixTime = float (tempInput)
        stimDict.update({'headFixTime' : headFixTime})
        # lick withold time
        lickWitholdTime = stimDict.get('lickWitholdTime', AHF_Stimulator_LickWitholdSpeaker.lickWitholdTime_def)
        tempInput = input ('set time needed to refrain from licking (currently {:.2f}) to:'.format (lickWitholdTime))
        if tempInput != '':
            lickWitholdTime = float (tempInput)
        stimDict.update({'lickWitholdTime' : lickWitholdTime})
        # withold time randomizer
        randomize_withold = stimDict.get('randomize_withold', AHF_Stimulator_LickWitholdSpeaker.randomize_withold_def)
        tempInput = input ('Randomize lick withold time (Yes or No currently {:s}) :'.format ('Y' if randomize_withold else 'N'))
        if tempInput != '':
            if tempInput[0].lower() == 'y':
                randomize_withold = True
            else:
                randomize_withold = False
        stimDict.update({'randomize_withold' : randomize_withold})
        # afterBuzz_withold time
        afterBuzz_withold = stimDict.get('afterBuzz_withold', AHF_Stimulator_LickWitholdSpeaker.afterBuzz_withold_def)
        tempInput = input ('Set time mouse mouse must refrain from licking AFTER the buzzer (currently {:.2f} seconds):'.format (afterBuzz_withold))
        if tempInput != '':
            afterBuzz_withold = float (tempInput)
        stimDict.update({'afterBuzz_withold' : afterBuzz_withold})
        # Lick window, time following afterBuzz withold time, where they NEED to lick
        lick_window = stimDict.get('lick_window', AHF_Stimulator_LickWitholdSpeaker.lick_window_def)
        tempInput = input ('Set duration of the time window where mice MUST lick to get a reward, or 0 to make reward non-contingent (currently {:2f} seconds.'.format (lick_window_def))
        if tempInput != '':
            lick_window = float (tempInput)
        stimDict.update({'lick_window' : lick_window})
        
        # ************************************ Buzzer settings**************************
        # GPIO pin
        buzz_pin = stimDict.get('buzz_pin', AHF_Stimulator_LickWitholdSpeaker.buzz_pin_def)
        tempInput = input ('set GPIO pin number for vibe motor buzzer (currently {:d}) to:'.format (buzz_pin))
        if tempInput != '':
            buzz_pin = int (tempInput)
        stimDict.update({'buzz_pin' : buzz_pin})
        # number of pulses
        buzz1_num = stimDict.get('buzz1_num', AHF_Stimulator_LickWitholdSpeaker.buzz1_num_def)
        tempInput = input ('set the number of pulses for vibe motor buzzer (currently {:d}) to:'.format (buzz1_num))
        if tempInput != '':
            buzz1_num = int (tempInput)
        stimDict.update({'buzz1_num' : buzz1_num})
        # length of each pulse
        buzz1_len = stimDict.get('buzz1_len', AHF_Stimulator_LickWitholdSpeaker.buzz1_len_def)
        tempInput = input ('Set the length of each pulse (currently {:.2f} seconds) to: '.format (buzz1_len))
        if tempInput != '':
            buzz1_len = float (tempInput)
        stimDict.update({'buzz1_len' : buzz1_len})
        # period - sum of ON and OFF times
        buzz1_period = stimDict.get ('buzz1_period', AHF_Stimulator_LickWitholdSpeaker.buzz1_period_def)
        tempInput = input ('Set the period (On time + OFF time) of each pulse (currently {:.2f} seconds) to: '.format (buzz1_period))
        if tempInput != '':
            buzz1_period = float (tempInput)
        stimDict.update({'buzz1_period' : buzz1_period})
        # ******************************************* Speaker settings ********************************************
        # GPIO pin for speaker
        speakerPin = stimDict.get('buzz_pin', AHF_Stimulator_LickWitholdSpeaker.speakerPin_def)
        tempInput = input ('set GPIO pin number for auditory feedback (currently {:d}) to:'.format (speakerPin))
        if tempInput != '':
            speakerPin = int (tempInput)
        stimDict.update({'speakerPin' : speakerPin})
        # speaker frequency
        speakerFreq = stimDict.get('buzz_pin', AHF_Stimulator_LickWitholdSpeaker.speakerFreq_def)
        tempInput = input ('set frequency for auditory feedback (currently {:.1f}) to:'.format (speakerFreq))
        if tempInput != '':
            speakerFreq = float (speakerFreq)
        stimDict.update({'speakerFreq' : speakerFreq})
        # duration when speaker is off after reward is given
        speakerOffForReward_def = stimDict.get('speakerOffForReward_def', AHF_Stimulator_LickWitholdSpeaker.speakerOffForReward_def_def)
        tempInput = input ('Set time mouse is given to consume reward with no speaker feedback (currently {:.2f} seconds):'.format (speakerOffForReward))
        if tempInput != '':
            speakerOffForReward = float (tempInput)
        stimDict.update({'speakerOffForReward' : speakerOffForReward})
                

    def setup (self):
        """
        copy frequently used settings from dictionary and Initialize GPIO outputs for buzzer and speaker
        """
        self.buzz_pin = self.expSettings.get (stimDict.buzz_pin)
        self.buzz1_len = self.expSettings.stimDict.get(buzz1_len)
        self.buzz1_delay = self.expSettings.stimDict.get(buzz1_period) - self.buzz1_len
        self.buzz1_num = self.expSettings.stimDict.get(buzz1_num)
        self.speakerPin = self.expSettings.stimDict.get(speakerPin)
        self.speakerPin = self.expSettings.stimDict.get(speakerPin)
        self.speakerFreq = self.expSettings.stimDict.get(speakerFreq)
        self.speakerDuty = AHF_Stimulator_LickWitholdSpeaker.speakerDuty_def
        self.speakerOffForReward = self.expSettings.stimDict.get(speakerOffForReward)
        self.headFixTime = self.expSettings.stimDict.get(headFixTime)
        self.lickWitholdTime = self.expSettings.stimDict.get(lickWitholdTime)
        self.randomize_withold = self.expSettings.stimDict.get(randomize_withold)
        if self.randomize_withold:
            self.scalerForRandom = min (0.5, lickWitholdTime/2)
        else:
            self.scalerForRandom = 0
        self.afterBuzz_withold = self.expSettings.stimDict.get(afterBuzz_withold)
        self.lick_window = self.expSettings.stimDict.get(lick_window)
        # make a train for buzzer 
        self.buzzer1=Train (PTSimpleGPIO.MODE_PULSES, self.buzz_pin, 0, self.buzz1_delay, self.buzz1_len, self.buzz1_num, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        # make an infinite train for speaker feedback
        self.speaker=Infinite_train (PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        self.buzzTimes = []
        self.lickWitholdTimes = []
        self.buzzTypes = []
        self.rewardTimes = []


    def configStim (self, mouse):
        """
        not much to do here, each trial in a session is its own thing 
        """
        self.mouse = mouse
        return 'lw'
        

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
            lickWitholdRandom = self.lickWitholdTime + (self.scalerForRandom * (0.5 - random ()))
            lickWitholdEnd = time() + lickWitholdRandom
            # inner loop keeps resetting lickWitholdEnd time until  a succsful withhold
            while time() < lickWitholdEnd and time() < endTime:
                anyLicks = self.lickDetector.wait_for_lick(0.05)
                if anyLicks == 0:
                    if speakerIsOn == True:
                        self.speaker.stop_train()
                        speakerIsOn = False
                else: # there were licks in witholding period, so reset lickWitholdEnd
                    lickWitholdEnd = time() + lickWitholdRandom
                    if speakerIsOn == False and time() > OffForRewardEnd: # play speaker unless speaker is set to off for reward consumption
                        self.speaker.start_train()
                        speakerIsOn = True
            # while loop only exits if trial time is up or lick witholding time passed with no licking
            if time() > endTime:
                break
            # at this point, mouse has just witheld licking for lickWitholdTime
            self.lickWitholdTimes.append (lickWitholdRandom)
            # Give a buzz.
            self.buzzTimes.append (time())
            self.buzzer1.do_train()
            # check for no licks in afterBuzzwithold time
            if self.afterBuzz_withold > 0:
                 if self.lickDetector.wait_for_lick(self.afterBuzz_withold): # failure, mouse licking before it should
                    self.speaker.start_train()
                    speakerIsOn = True
                    self.buzzTypes.append (-4)
                    break
            # check for licks within lick_window
            if self.lick_window > 0:
                if not self.lickDetector.wait_for_lick(self.lick_window): # failure, mouse not licking when it should
                    self.buzzTypes.append (-2)
                    break
            # give a reward
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            self.buzzTypes.append (2)
            OffForRewardEnd = time() + self.speakerOffForReward # set time where speaker does not play 
        # on exit from outer loop, make sure to turn off buzzer
        if speakerIsOn == True:
            self.speaker.stop_train()
        # update info in dictionary for this mouse
        HFrewards = self.mouse.stimResultsDict.get('HFrewards', 0)
        self.mouse.stimResultsDict.update ({'HFrewards' : HFrewards + len (self.rewardTimes)})
        stimArray = self.mouse.stimResultsDict.get('buzzTypes', [0,0,0,0,0,0]) # -4, -3, -2 -1, 1, 2
        for buzz in self.buzzTypes:
            if buzz == -4:
                stimArray [0] += 1
            elif buzz == -2:
                stimArray [2] += 1
            elif buzz == 2:
                stimArray [5] += 1
        self.mouse.stimResultsDict.update ({'buzzTypes', stimArray})


    def logfile (self):
        """
        prints to the logfile and the shell the time duration of each lick withold event and the result of corresponding lick withold trial, plus time of each reward
        """
        buzz1Str = 'N={:d},length={:.2f},period={:.2f}'.format (self.buzz1_num, self.buzz1_len, self.buzz1_len + self.buzz1_delay) 
        for iBuzz in range (0, len (self.buzzTimes)):
            isoForm = datetime.fromtimestamp(int (self.buzzTimes [iBuzz])).isoformat (' ')
            # print mouse, time stamp, event, formatted time to the log file
            if self.expSettings.logFP != None:
                self.expSettings.logFP.write('{:013}\t{:.2f}\tBuzz:LickWitholdTime={:.2f},GO={:d},{:s}\t{:s}\n'.format (self.mouse.tag, self.buzzTimes [iBuzz], self.lickWitholdTimes [iBuzz], self.buzzTypes [iBuzz], buzz1Str, isoForm))
            # print mouse, formatted time, event to the shell
            print ('{:013}\t{:s}\tBuzz:LickWitholdTime={:.2f},GO={:d},{:s}'.format (self.mouse.tag, isoForm, self.lickWitholdTimes [iBuzz], self.buzzTypes [iBuzz], buzz1Str))

        for rewardTime in self.rewardTimes:
            isoForm = datetime.fromtimestamp(int (rewardTime)).isoformat (' ')
            # print mouse, time stamp, event, formatted time to the log file
            if self.expSettings.logFP != None:
                self.expSettings.logFP.write('{:013}\t{:.2f}\tHeadFixReward\t{:s}\n'.format (self.mouse.tag, rewardTime, isoForm))
            # print mouse, formatted time, event to the shell
            print ('{:013}\t{:s}\tHeadFixReward'.format (self.mouse.tag, isoForm))
 
        if self.expSettings.logFP != None:
            self.textfp.flush()


    def tester(self,expSettings):
        """
        Tester function called from the hardwareTester. Includes Stimulator
        """
        while(True):
            inputStr = input ('v = vib. motor, s= speaker, q= quit: ')
            if inputStr == 's':
                self.speaker.start_train()
                sleep(3)
                self.speaker.stop_train()
            elif inputStr == 'v':
                self.buzzer.do_train()
            elif inputStr == 'q':
                break

    def inspect_mice(self,mice,cageSettings,expSettings):
        #Inspect the mice array
        print('MouseID\t\theadFixStyle\tstimType')
        for mouse in mice.mouseArray:
            headFixStyle = 'fix'
            if mouse.headFixStyle == 1:
                headFixStyle = 'loose'
            elif mouse.headFixStyle == 2:
                headFixStyle = 'nofix'
            stimType = expSettings.stimulator[mouse.stimType][15:22]
            print(str(mouse.tag)+'\t'+headFixStyle + '\t\t' + stimType)
        while(True):
            inputStr = input ('c= headFixStyle, s= stimType, q= quit: ')
            if inputStr == 'c':
                while(True):
                    inputStr =  int(input ('Type the tagID of mouse to change headFixStyle:'))
                    for mouse in mice.mouseArray:
                        if mouse.tag == inputStr:
                            inputStr = int(input('Change headFixStyle to:\n0: fix\n1: loose\n2: nofix\n'))
                            if inputStr == 0:
                                mouse.headFixStyle = 0
                            elif inputStr == 1:
                                mouse.headFixStyle = 1
                            elif inputStr == 2:
                                mouse.headFixStyle = 2

                    inputStr = input('Change value of another mouse?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        continue
                    else:
                        break

            elif inputStr == 's':
                while(True):
                    inputStr =  int(input ('Type the tagID of mouse to change stimType:'))
                    for mouse in mice.mouseArray:
                        if mouse.tag == inputStr:
                            print('Following stimTypes are available:')
                            for i,j in enumerate(expSettings.stimulator):
                                print(str(i)+': '+j[15:])
                            inputStr = int(input('Change stimType to:'))
                            mouse.stimType = inputStr

                    inputStr = input('Change value of another mouse?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        continue
                    else:
                        break
                    
            elif inputStr == 'q':
                break
