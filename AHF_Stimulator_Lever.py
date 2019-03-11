 #! /usr/bin/python
#-*-coding: utf-8 -*

import ptLeverThread
from array import array
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse
from Pywith import Pulse, Train
import time
import json


# a1 =lt.posBuffer[68:75] + lt.posBuffer [0:67] + lt.posBuffer [68:120]
class AHF_Stimulator_Lever (AHF_Stimulator):
    """
        AHF_Stimulator_Lever runs a lever task by calling ptLeverThread C-module code that
        records lever position and puts torque on the lever
    """
    ZERO_LEVER_RETURN = 0
    ZERO_LEVER_RESET = 1
    LEVER_FREQ = 250
    
    posBufferSize_def = 1000 # 4 seconds of lever position data at 250 Hz
    isCued_def = False # trials will be un-cued, mouse starts when he likes
    toGoalOrCirc_def = 63 # .252 seconds before lever gets into goal are recorded
    isReversed_def = False # decoder numbers get bigger when mouse pulls lever
    goalCuePin_def = 23 # GPIO pin to use for a cue when lever is in goal pos
    goalCueFreq_def = 0 # frequency for goal cue - 0 means DC, i.e., turn ON and OFF
    constForce_def = 1300 # constant force on lever
    pathToData_def = '/home/pi/Documents/' # folder where lever pos files will be saved

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
