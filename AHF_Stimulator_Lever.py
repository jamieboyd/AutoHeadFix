 #! /usr/bin/python
#-*-coding: utf-8 -*

import ptLeverThread
from array import array

from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse

import time
import json

class AHF_Stimulator_Lever (AHF_Stimulator):
    """
        AHF_Stimulator_Lever runs a lever task by calling c++ code that
        records lever position and puts torque on the lever
    """
    ZERO_LEVER_RETURN = 0
    ZERO_LEVER_RESET = 1
    
    posBufferSize_def = 1000 # 4 seconds of lever position data at 250 Hz
    isCued_def = False # trials will be un-cued, mouse starts when he likes
    toGoalOrCirc_def = 63 # .252 seconds before lever gets into goal are recorded
    isReversed_def = False # decoder numbers get bigger when mouse pulls lever
    goalCuePin_def = 23 # GPIO pin to use for a cue when lever is in goal pos
    goalCueFreq_def = 0 # frequency for goal cue - 0 means DC, i.e., turn ON and OFF
    constForce_def = 1300 # constant force on lever
    pathToData_def = '/home/pi/Documents/' # folder where lever pos files will be saved

    
    def __init__ (self, configDict, rewarder, lickDetector, textfp):
        super().__init__(configDict, rewarder, lickDetector, textfp)
        self.posBufferSize=int(self.configDict.get ('posBufferSize', AHF_Stimulator_Lever.posBufferSize_def))
        self.isCued = bool (self.configDict.get ('isCued', AHF_Stimulator_Lever.isCued_def))
        self.constForce = int (self.configDict.get ('constForce', AHF_Stimulator_Lever.constForce_def))
        self.toGoalOrCirc = int (self.configDict.get ('toGoalOrCirc', AHF_Stimulator_Lever.isCued_def))
        self.isReversed = bool (self.configDict.get ('isReversed', AHF_Stimulator_Lever.isReversed_def))
        self.goalCuePin = int (self.configDict.get ('goalCuePin', AHF_Stimulator_Lever.goalCuePin_def))
        self.goalCueFreq = float (self.configDict.get('goalCueFreq', AHF_Stimulator_Lever.goalCueFreq_def))
        self.pathToData = str (self.configDict.get ('pathToData', AHF_Stimulator_Lever.pathToData_def))
        # make unsigned byte array of position data
        self.posArray = array ('B', [0] * self.posArraySize)
        # make or open output file for today
        now = datetime.fromtimestamp (int (time()))
        startDay = datetime (now.year, now.month,now.day, kDAYSTARTHOUR,0,0)
        filename = self.pathToData + 'Lever_' + str (startDay.year) + '_' + '{:02}'.format(startDay.month)+ '_' + '{:02}'.format (startDay.day)
        self.outFile=open (filename, 'ab')
        # make the lever thread that does the lever access
        self.leverThread = ptLeverThread.new (self.posArray, self.isCued, self.toGoalOrCirc, self.isReversed, self.goalCuePin, self.goalCueFreq)
        # set constant force
        ptLeverThread.setConstForce(self.leverThread, self.constForce)
        # Zero the lever, resetting the zero point
        self.zeroLever (self.ZERO_LEVER_RESET)
        ptLeverThread.zeroLever(self.leverThread, self.ZERO_LEVER_RESET, 0)
        

    @staticmethod
    def dict_from_user (stimDict):
        keyTuple = ('posBufferSize', 'isCued', 'constForce', 'toGoalOrCirc', 'isReversed', 'goalCuePin', 'goalCueFreq','pathToData')
        for key in keyTuple:
            value = input ('Enter a value for ' + key + ':')
            stimDict.update({key : value})



    

    def setConstForce (self, newForce):
        ptLeverThread.setConstForce(self.leverThread, newForce)

    
    def getConstForce (self):
        return ptLeverThread.getConstForce(self.leverThread)


    def applyForce (self, theForce):
        ptLeverThread.applyForce(self.leverThread, theForce)

    def applyConstForce(self):
        ptLeverThread.applyConstForce (self.leverThread)

    def zeroLever (self, zeroMode):
        return ptLeverThread.zeroLever(self.leverThread, zeroMode, 0)

    def setPerturbForce (self, perturbForce):
        ptLeverThread.setPerturbForce(self.leverThread, perturbForce)

    def setPerturbStartPos (self, startPos):
        ptLeverThread.setPerturbStartPos(self.leverThread, startPos)

    def startTrial (self):
        ptLeverThread.startTrial(self.leverThread)

    def checkTrial (self):
        resultTuple = ptLeverThread.checkTrial(self.leverThread)
        self.trialComplete = resultTuple [0]
        self.trialPos = resultTuple [1]
        self.inGoal = resultTuple [2]
        return resultTuple
    
    def turnOnGoalCue (self):
        ptLeverThread.doGoalCue(self.leverThread, 1)
    
    def turnOffGoalCue (self):
        ptLeverThread.doGoalCue(self.leverThread, 0)


    def setHoldParams(self, goalBottom, goalTop, nHoldTicks):
        ptLeverThread.setHoldParams (self.leverThread, goalBottom, goalTop, nHoldTicks)

    def getLeverPos (self):
        return ptLeverThread.getLeverPos(self.leverThread)

    def abortUnCuedTrial(self):
        ptLeverThread.abortUncuedTrial(self.leverThread)

    def isCued (self):
        return ptLeverThread.isCued (self.leverThread)

    def setCued (self, isCued):
        return ptLeverThread.setCued (self.leverThread, isCued)
