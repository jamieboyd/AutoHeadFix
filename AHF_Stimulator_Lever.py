 #! /usr/bin/python
#-*-coding: utf-8 -*

import ptLeverThread
from array import array
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
import time
import json


# a1 =lt.posBuffer[68:75] + lt.posBuffer [0:67] + lt.posBuffer [68:120]
class AHF_Stimulator_Lever (AHF_Stimulator):
    """
    AHF_Stimulator_Lever runs a lever task by calling ptLeverThread C-module code that records lever position and puts torque on the lever
    """
    LEVER_FREQ = 250 # as set in leverThread.h when ptLeverThread c module is compiled

    defaultRecordingTime = 4 # 4 seconds of lever position data
    defaultTrialIsCued = False # trials will be un-cued, mouse starts when he likes
    defaultToGoalTime = .25 # previous .25 seconds before lever gets into goal are recorded for uncued trials/mouse has .25 seconds from cue
    defaultIsReversed = False # decoder numbers get bigger when mouse pulls lever
    defaultStartCuePin = 27 # GPIO pin to use for a cue when mouse should start a trial
    defaultStartCueFreq = 0 # frequency for start cue - 0 means DC, i.e., turn ON and OFF
    defaultStartCueDur = 0.1 # duration in seconds of start cue
    defaultTrialTimeout = 0.5 # time in seconds between end of one trial (ended for any reason) and start of the next
    defaultGoalCuePin = 23 # GPIO pin to use for a cue when lever is in goal pos
    defaultGoalCueFreq = 0 # frequency for goal cue - 0 means DC, i.e., turn ON and OFF
    defaultConstForce = 1300 # constant force on lever, a 12 bit value, 0 to 4095
    #pathToData_def = '/home/pi/Documents/' # folder where lever pos files will be saved
    
    @staticmethod
    def about():
        return 'Lever stimulator records lever position and puts torque on the lever by calling ptLeverThread C-module'
        
    @staticmethod
    def config_user_get (starterDict = {}):
        recordingTime = starterDict.get ('recordingTime', AHF_Stimulator_Lever.defaultRecordingTime)
        response = input('Enter the maximum time for a lever recording in seconds (currently {:.2f}): '.format (recordingTime))
        if response != '':
            recordingTime = float (response)
        trialIsCued = StarterDict.get ('trialIsCued', AHF_Stimulator_Lever.defaultTrialIsCued)
        response = input ('Do the lever pull trials have a start cue? (yes or no, currently {:.str}): '.format ('Yes' if mybool else 'No'))
        if response != '':
            trialIsCued = True if response [0] == 'y' or response [0] == 'Y' else False
        if trialIsCued:
            
        
        rewardInterval = starterDict.get ('rewardInterval', AHF_Stimulator_Lever.defaultInterval)
        response = input ('Enter the time interval between rewards (currently %.2f seconds): ' % rewardInterval)
        if response != '':
            rewardInterval = float (response)
        starterDict.update({'nRewards' : nRewards, 'rewardInterval' : rewardInterval})
        return starterDict



    def config_user_get (starterDict = {}):

        keyTuple = ('posBufferSize', 'isCued', 'constForce', 'toGoalOrCirc', 'isReversed', 'goalCuePin', 'goalCueFreq','pathToData')
        for key in keyTuple:
            value = input ('Enter a value for ' + key + ':')
            stimDict.update({key : value})

     @staticmethod
    def dict_from_user (stimDict):
        if not 'dataSaveFolder' in stimDict:
            stimDict.update ({'dataSaveFolder' : '/home/pi/Documents/'})

        if not 'decoderReversed' in stimDict:
            stimDict.update ({'decoderReversed' : False})
        if not 'motorPresent' in stimDict:
            stimDict.update ({'motorPresent' : True})
        if not 'motorHasDirection' in stimDict:
            stimDict.update ({'motorHasDirection' : True})
        if not 'motorDirectionPin' in stimDict:
            stimDict.update ({'motorDirectionPin' : 18})
        if not 'startCuePin' in stimDict:
            stimDict.update ({'startCuePin' : 17})
        return super(AHF_Stimulator_Lever, AHF_Stimulator_Lever).dict_from_user (stimDict)
