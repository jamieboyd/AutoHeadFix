'''
This Stimulator combines LaserStimulation with LickWitholdSpeaker.
It captures a reference image for each mouse and includes a user interface to select targets on reference images.
The Stimulator directs and pulses a laser to selected targets for optogenetic
stimulation/inhibition.
The laser is pulsed whenever the mouse goes for a set amount of time without licking,
'''

#AHF-specific moudules

from AHF_Stimulus_Laser import AHF_Stimulus_Laser
from PTSimpleGPIO import PTSimpleGPIO, Infinite_train, Train
from random import random
import RPi.GPIO as GPIO

#Laser-stimulator modules
from pynput import keyboard
import numpy as np
import sys
import matplotlib.pyplot as plt
from PTPWM import PTPWM
from array import array
from queue import Queue as queue
from threading import Thread
from multiprocessing import Process, Queue
from time import sleep, time
from random import random
from datetime import datetime
from itertools import combinations,product
import imreg_dft as ird
import warnings




class AHF_Stimulator_LickWithold (AHF_Stimulator):
    #### default definitions for stimulator configuration that are not defined in superclass
    lickWitholdTime_def = 1  # how long mouse has to go for without licking before getting rewarded
    stim_lead_def = 0.5     # laser pulse is this may seconds before reward is given
    ##### speaker feedback GPIO definitions #######
    speakerPin_def = 25      # GPIO pin used to drive piezo speaker for negative feedback
    speakerFreq_def = 300    # frequency to drive the speaker
    speakerDuty_def = 0.8    # duty cycle to drive speaker, unbalanced duty cycle gives nasty harmonics
    speakerOffForReward_def = 1.5   #time for consuming reward without getting buzzed at

    def config_user_get (starterDict = {}):
        lickWitholdTime = starterDict.get ('lickWitholdTime', AHF_Stimulator_Laser_LW.lickWitholdTime_def)
        tempInput = input ('Set lick withold time (currently {0}): '.format(lickWitholdTime))
        if tempInput != '':
            lickWitholdTime = float (tempInput)
        starterDict.update ({'lickWitholdTime' : lickWitholdTime})
        stim_lead = starterDict.get ('stim_lead',AHF_Stimulator_Laser_LW.stim_lead_def)
        tempInput = input ('Set stimulus lead time (time between stimulus and reward, currently {0}): '.format(stim_lead))
        if tempInput != '':
            stim_lead = float (tempInput)
        starterDict.update ({'stim_lead' : stim_lead})
        speakerPin = starterDict.get ('speakerPin', AHF_Stimulator_Laser_LW.speakerPin_def)
        tempInput = input ('Set speaker pin (currently {0}): '.format(speakerPin))
        if tempInput != '':
            speakerPin = int (tempInput)
        starterDict.update ({'speakerPin' : speakerPin})
        speakerFreq = starterDict.get ('speakerFreq', AHF_Stimulator_Laser_LW.speakerFreq_def)
        tempInput = input ('Set speaker frequency (currently {0}): '.format(speakerFreq))
        if tempInput != '':
            speakerFreq = int (tempInput)
        starterDict.update ({'speakerFreq' : speakerFreq})
        speakerDuty = starterDict.get ('speakerDuty', AHF_Stimulator_Laser_LW.speakerDuty_def)
        tempInput = input ('Set speaker duty cycle (currently {0}): '.format(speakerDuty))
        if tempInput != '':
            speakerDuty = int (tempInput)
        starterDict.update ({'speakerDuty' : speakerDuty})
        speakerOffForReward = starterDict.get ('speakerOffForReward', AHF_Stimulator_Laser_LW.speakerOffForReward_def)
        tempInput = input ('Set time to have speaker off while rewarding (currently {0}): '.format(speakerOffForReward))
        if tempInput != '':
            speakerOffForReward = int (tempInput)
        starterDict.update ({'speakerOffForReward' : speakerOffForReward})

        return starterDict

    def setup (self):
        # super() sets up all the laser stuff plus self.headFixTime plus # rewards (not used here)
        super().setup()
        #Lick-withold settings
        self.lickWitholdTime = float (self.settingsDict.get ('lickWitholdTime', self.lickWitholdTime_def))
        self.stim_lead = float (self.settingsDict.get ('stim_lead', self.stim_lead_def))
        # setting up speaker for negative feedback for licking
        self.speakerPin=int(self.settingsDict.get ('speakerPin', self.speakerPin_def))
        self.speakerFreq=float(self.settingsDict.get ('speakerFreq', self.speakerFreq_def))
        self.speakerDuty = float(self.settingsDict.get ('speakerDuty', self.speakerDuty_def))
        self.speakerOffForReward = float(self.settingsDict.get ('speakerOffForReward', self.speakerOffForReward_def))
        self.speaker=Infinite_train (PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        #Mouse scores
        self.lickWitholdTimes = []
        self.rewardTimes = []
        self.laserTimes = []


#=================Main functions called from outside===========================
    def run(self, level = 0, resultsDict = {}, settingsDict = {}):
        self.tag = self.task.tag
        self.mouse = self.task.Subjects.get(self.tag)
        self.loadH5()
        self.lickWitholdTimes = []
        self.rewardTimes = []
        self.laserTimes = []
        if self.task.isFixTrial:

            try:
                self.task.Stimulus.trialPrep()

                #every time lickWitholdtime passes with no licks, make a buzz then give a reward after buzz_lead time.
                self.lickWitholdTimes = []
                self.rewardTimes = []
                self.laserTimes = []
                endTime = time() + self.mouse.get('headFixTime', 40)
                speakerIsOn = False
                OffForRewardEnd = 0.0
                while time() < endTime:
                    # setup to start a trial, witholding licking for lickWitholdRandom secs till buzzer
                    lickWitholdRandom = self.lickWitholdTime + (0.5 - random())
                    lickWitholdEnd = time() + lickWitholdRandom
                    # inner loop keeps resetting lickWitholdEnd time until  a succsful withhold
                    while time() < lickWitholdEnd and time() < endTime:
                        anyLicks = self.task.LickDetector.waitForLick (0.05)
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
                    # inner while loop only exits if trial time is up or lick witholding time passed with no licking
                    if anyLicks > 0:
                        break
                    # at this point, mouse has just witheld licking for lickWitholdTime
                    self.lickWitholdTimes.append (lickWitholdRandom)
                    # Give a laser pulse
                    if targ_pos is not None:
                        self.laserTimes.append (time())
                        self.task.Stimulus.stimulate()
                        self.task.DataLogger.writeToLogFile (self.tag, 'Stimulus', None, time())
                    # sleep for lead time, then give reward
                    sleep (self.stim_lead)
                    self.rewardTimes.append (time())
                    self.rewarder.giveReward('task')
                    #print ('{:013}\t{:s}\treward'.format(self.mouse.tag, datetime.fromtimestamp (int (time())).isoformat (' ')))

                    OffForRewardEnd = time() + self.speakerOffForReward
                # make sure to turn off buzzer at end of loop when we exit
                if speakerIsOn == True:
                    self.speaker.stop_train()
                newRewards = resultsDict.get('rewards', 0) + len (self.rewardTimes)
                resultsDict.update({'rewards': newRewards})
                self.camera.stop_preview()

                """
                # Repeatedly give a reward and pulse simultaneously
                timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
                self.rewardTimes = []
                self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
                for reward in range(self.nRewards):
                    self.rewardTimes.append (time())
                    if targ_pos is not None:
                        self.pulse(self.laser_on_time,self.duty_cycle)
                        writeToLogFile(self.expSettings.logFP, self.mouse, 'laser pulse')
                    self.rewarder.giveReward('task')
                    sleep(timeInterval)
                self.mouse.headFixRewards += self.nRewards
                self.camera.stop_preview()
                """
            finally:
                #Move laser back to zero position at the end of the trial
                self.move_to(np.array([0,0]),topleft=True,join=False)
        else:
            timeInterval = self.rewardInterval #- self.rewarder.rewardDict.get ('task')
            self.rewardTimes = []
            self.camera.start_preview()
            for reward in range(self.nRewards):
                self.rewardTimes.append (time())
                self.rewarder.giveReward('task')
                sleep(timeInterval)
            newRewards = resultsDict.get('rewards', 0) + self.nRewards
            resultsDict.update({'rewards': newRewards})
            self.camera.stop_preview()


#==== High-level Utility functions: Matching of coord systems, target selection and image registration ====
