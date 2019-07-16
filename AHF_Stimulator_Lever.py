 #! /usr/bin/python
#-*-coding: utf-8 -*

import ptLeverThread
from PTSimpleGPIO import PTSimpleGPIO, Pulse, Train, Infinite_train
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse, Mice
import AHF_ClassAndDictUtils as CAD
from time import time
from array import array

import RPi.GPIO as GPIO

class AHF_Stimulator_Lever (AHF_Stimulator):
    """
    AHF_Stimulator_Lever runs a lever task by calling c++ code that records lever position and puts torque on the lever
    """
    LEVER_FREQ = 250 # as set in leverThread.h when ptLeverThread c module is compiled. Frequency in Hz of updating lever position and lever force
    MAX_FORCE_ARRAY_SIZE = 125 # as set in leverThread.h when ptLeverThread c module is compiled. Maximum size of array for calculating perturb force ramp
    """
    ######################################### Global settings for the task########################################################
    Things that do not vary on a per mouse basis, these inlcude hardware settings, some trial timing
    """
    defaultRecordingTime = 4 #  maximum of seconds of lever position data that will be recorded per trial
    defaultLeverIsReversed = False # False means lever position numbers start at 0 and get bigger when mouse pulls lever, True means numbers get smaller
    defaultGoalCuePin = 23 # GPIO pin to use for a cue played when lever is in goal pos
    defaultGoalCueFreq = 0 # frequency for goal cue - 0 means DC, i.e., turn ON and OFF
    defaultConstForce = 0.3 # constant force on lever at start of trial that mouse must pull against, as opposed to perturbForce set during a trial a 12 bit value, 0 to 4095
    defaultTrialIsCued = False # True means trials will be started with the start cue; False means mouse starts pulling lever whenever he likes
    defaultMotorEnable = 20 # GPIO Pin to enable motor
    defaultMotorIsReversed = False
    defaultMotorDir = 0
    """
    If MOTOR_DIR_PIN = 0, 16 bit force output (0 - 4095) goes from full counterclockwise force to full clockwise force
    with midpoint (2048) being no force on lever. If MOTOR_DIR_PIN is non-zero, 0-4095 maps from  no force to full force, and
    MOTOR_DIR_PIN is the GPIO pin that controls the direction of the force, clockwise or counter-clockwise.
    """
    """
    Settings for cued trials
    """
    defaultStartCuePin = 27 # GPIO pin to use for a cue when mouse should start a trial, this can be a pulse (freq =0) or a train
    defaultStartCueFreq = 0 # frequency for start cue - 0 means DC, i.e., turn ON and OFF
    defaultStartCueDur = 0.1 # duration in seconds of start cue
    defaultTrialTimeout = 0.5 # time in seconds between end of one trial (ended for any reason) and start of the next trial. Lever is rezeroed here
    """
    Settings for uncued trials
    """
    defaultPrePullTime = 0.25 # this many seconds of time before the lever reaches goal position is saved in a circular buffer
    """
    ############################################# Mouse Specific Settings follow #####################################################
    default pull difficulty settings for starting a mouse
    toGoalTime plus holdTime must be < recordingTime for cued trials. PrePullTime plus holdTime must be < recordingTime for un-cued trials
    """
    defaultToGoalTime = .25 # mouse has this many seconds from start cue (cued trials only)to get lever into goal area, or trial is ended.
    defaultHoldTime = 0.2 # mouse must hold lever in goal area for this long for success, can be overridden by training settings
    defaultGoalCenter = 200 # center of goal area where mouse must maintain lever for success
    defaultGoalWidth = 100 # width of goal area where mouse must maintain lever for success, can be overridden by training settings
    """
    Perturbation settings for starting a mouse. Force on lever is adjusted up or down relative to const force, and then left at new value, and lever must be kept in goal area
    """
    defaultPerturbPercent = 0.0 # 0 means no perturbation, just hold lever in goal area for hold time, non-zero value (0-1) means proportion of trials to perturb
    defaultPerturbRampDur = 0.25 # duration of ramp for perturbationb, in seconds, max possible duration is set by MAX_FORCE_ARRAY_SIZE / LEVER_FREQ
    defaultPerturbStartTime = 1# time from ToGoalTime to start of perturbation
    defaultPerturbStartRandom = 0 # 0 randomized time in seconds plus/minus applied to perturbStart time, 0 means do not randomize perturb start time
    defaultPerturbForceOffset = 0 # added force on lever during a perturbation relative to constant force. If perturbForceOffset is 0, randomized force is symetric around constantForce
    defaultPerturbForceRandom = 400 # randomized force range plus/minus applied to constantForce + perturb force, 0 means do not randomize
    """
    Training settings
    """
    defaultTrainSize = 50 # number of previous trials to examine when deciding promotion/demotion
    defaultPromoteRate = 0.75 # promote to next level when this performance rate is exceeded
    defaultDemoteRate = 0.25 # drop to previous level when fail rate is not met
    """
    training for goal position
    """
    defaultGoalTrainOn = 0 # bit 0 means training, bit 1 means demotion is not allowed, only promotion to next level
    defaultGoalStartWidth = 100
    defaultGoalEndWidth = 10
    defaultGoalIncr = 5
    """
    training for holdTime
    """
    defaultHoldTrainOn = False
    defaultHoldStartTime = 0.1
    defaultHoldEndTime = 2
    defaultHoldIncr = 0.1

    @staticmethod
    def about():
        return 'As mice hold a lever in a set angular range, Lever stimulator records lever position and puts torque on the lever by calling ptLeverThread C-module.'


    @staticmethod
    def dict_from_user (stimDict = {}):
        recordingTime = starterDict.get ('recordingTime', AHF_Stimulator_Lever.defaultRecordingTime)
        response = input('Enter the maximum time in seconds of lever position data that will be recorded per trial(currently {:.2f}): '.format (recordingTime))
        if response != '':
            recordingTime = float (response)

        leverIsReversed = starterDict.get ('leverIsReversed', AHF_Stimulator_Lever.defaultLeverIsReversed)
        response = input ('Is the lever direction reversed ?, (Yes or No, currently {:s}): '.format ('Yes' if leverIsReversed else 'No'))
        if response != '':
            leverIsReversed = True if response [0] == 'y' or response [0] == 'Y' else False

        goalCuePin = starterDict.get ('goalCuePin', AHF_Stimulator_Lever.defaultGoalCuePin)
        response = input('Enter the GPIO pin to use for a cue played whenever lever is in the goal position (currently {:d}): '.format (goalCuePin))
        if response != '':
            goalCuePin = int (response)

        goalCueFreq = starterDict.get ('goalCueFreq', AHF_Stimulator_Lever.defaultGoalCueFreq)
        response = input ('Enter the frequency in Hz to use for the goal cue - 0 turn ON and OFF (currently {:.2f}): '.format (goalCueFreq))
        if response != '':
            goalCueFreq = float (response)

        constForce = starterDict.get ('constForce', AHF_Stimulator_Lever.defaultConstForce)
        response = input ('Enter the constant force applied to the on lever at the start of a trial, from 0 to 1.0 (currently {:.2f}): '.format (constForce))
        if response != '':
            constForce = float (response)

        motorEnable = starterDict.get ('motorEnable', AHF_Stimulator_Lever.defaultMotorEnable)
        response = input ('Enter the GPIO pin to enable the motor (currently {:d}): '.format (motorEnable))
        if response != '':
            motorEnable = int (response)

        motorIsReversed = starterDict.get ('motorIsReversed', AHF_Stimulator_Lever.defaultMotorIsReversed)
        response = input ('Is the motor direction reversed ?, (Yes or No, currently {:s}): '.format ('Yes' if motorIsReversed else 'No'))
        if response != '':
            motorIsReversed = True if response [0] == 'y' or response [0] == 'Y' else False

        motorDir = starterDict.get ('motorDir', AHF_Stimulator_Lever.defaultMotorDir)
        response = input ('Enter the GPIO pin to control force direction, 0 for both directions, currently {:d} '.format (motorDir))
        if response != '':
            motorDir = int (response)

        trainSize = starterDict.get ('trainSize', AHF_Stimulator_Lever.defaultTrainSize)
        response = input('Enter the number of previous trials to examine when deciding promotion/demotion (currently {:d}): '.format (trainSize))
        if response != '':
            trainSize = int (response)

        trialIsCued = starterDict.get ('trialIsCued', AHF_Stimulator_Lever.defaultTrialIsCued)
        response = input ('Do the lever pull trials have a start cue? (yes or no, currently {:s}): '.format ('Yes' if trialIsCued else 'No'))
        if response != '':
            trialIsCued = True if response.lower()[0] == 'y' else False
        starterDict.update({'recordingTime': recordingTime, 'leverIsReversed': leverIsReversed, 'goalCuePin': goalCuePin, 'goalCueFreq': goalCueFreq})
        starterDict.update({'constForce': constForce, 'trialIsCued': trialIsCued, 'trainSize': trainSize})
        starterDict.update({'motorIsReversed': motorIsReversed, 'motorDir': motorDir, 'motorEnable': motorEnable})
        if trialIsCued:
            startCuePin = starterDict.get ('startCuePin', AHF_Stimulator_Lever.defaultStartCuePin)
            response = input ('Enter the GPIO pin to use for cues, currently {:d}: '.format (startCuePin))
            if response != '':
                startCuePin = int (response)

            startCueFreq = starterDict.get ('startCueFreq', AHF_Stimulator_Lever.defaultStartCueFreq)
            response = input ('Enter the frequency to use for cues, currently {:d}: '.format (startCueFreq))
            if response != '':
                startCueFreq = int (response)

            startCueDur = starterDict.get ('startCueDur', AHF_Stimulator_Lever.defaultStartCueDur)
            response = input ('Enter the duration of cues, currently {:.2f}: '.format (startCueDur))
            if response != '':
                startCueDur = float (response)

            trialTimeout = starterDict.get ('trialTimeout', AHF_Stimulator_Lever.defaultTrialTimeout)
            response = input ('Enter the time between trials, currently {:.2f}: '.format (trialTimeout))
            if response != '':
                trialTimeout = float (response)
            starterDict.update({'startCuePin': startCuePin, 'startCueFreq': startCueFreq, 'startCueDur': startCueDur, 'trialTimeout': trialTimeout})
        else:
            #defaultPrePullTime = 0.25 # this many seconds of time before the lever reaches goal position is saved in a circular buffer
            prePullTime = starterDict.get ('prePullTime', AHF_Stimulator_Lever.defaultPrePullTime)
            response = input ('Enter the duration prior to goal position to be saved, currently {:.2f}: '.format (prePullTime))
            if response != '':
                prePullTime = float (response)
            starterDict.update({'prePullTime': prePullTime})

        return starterDict


    def setup (self):  # make the lever thread that does the lever access
        # set up GPIO pin for start cue, if cued
        self.motorEnablePin = self.expSettings.stimDict.motorEnable
        self.isCued = self.expSettings.stimDict.trialIsCued
        if self.isCued:
            self.cuePin = self.expSettings.stimDict.startCuePin
            if self.expSettings.stimDict.startCueFreq == 0:
                self.cueMode = 0
                cuer = Pulse (self.expSettings.stimDict.startCuePin, 0, 0, self.expSettings.stimDict.startCueDur, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS):
            else:
                self.cueMode = 1
                cuer = Train (PTSimpleGPIO.MODE_FREQ, self.expSettings.stimDict.startCuePin, 0, self.expSettings.stimDict.startCueFreq, 0.5, self.expSettings.stimDict.startCueDur, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS):
        # set up GPIO pin for motor enable
        GPIO.setmode (GPIO.BCM)
        self.motorEnablePin = self.expSettings.stimDict.motorEnable
        GPIO.setup(self.motorEnablePin, GPIO.OUT)
        # make signed word array shared with ptleverThread
        self.posBuffer = array.array('h', [0]*self.expSettings.stimDict)
        # make ptLeaverThread
        self.leverThread = ptLeverThread.new (self.posArray, self.expSettings.stimDict.isCued, self.expSettings.stimDict.toGoalOrCirc, self.expSettings.stimDict.isReversed, self.expSettings.stimDict.goalCuePin, self.expSettings.stimDict.goalCueFreq)
         # set constant force
        ptLeverThread.setConstForce(self.leverThread, self.expSettings.stimDict.constForce)
         # Zero the lever, resetting the zero point
        ptLeverThread.zeroLever(self.leverThread, 1, 0)
        

    def configStim (self, mouse):
        """
        gets a lever stimulus ready by reading dictionary for this mouse
        """
        self.mouse = mouse
        mouse.stimResultsDict
        


    def tester (self, mice):
        """
        Tester function to called from the hardwareTester. Allows setting paramaters and adjusting settings for mice
        
        :param mice: reference to mice so stimulator can edit results/settings dictionary for mice
        """
        while True:
            response = int (input('Enter 1 to edit global settings, 2 to edit mouse-specific settings, 0 to exit'))
            if reponse = 0:
                break
            elif response == 1:
                CAD.Edit_dict (self.expSettings.stimDict, '{:s} Stimulator'.format(self.__class__.__name__.lstrip('AHF_Stimulator_')))
            elif response = 2:
                while True:
                    print ('****************** Existing Mice ***************************')
                    iMouse = 0
                    mArray = []
                    for mouse in mice.generator():
                        print ('{:d}) {:d}'.format (iMouse, mouse.tag))
                        mArray.append(mouse)
                        iMouse +=1
                    response = int (input ('Enter number of mouse for testing/editing, -1 to add a mouse, or -2 to exit:'))
                    if response == -2:
                        break
                    elif response == -1:
                        tagNum = 
                    elif reponse < iMouse:
                        theMouse = mArray [response]
                        theMouse.stimResultsDict = self.config_user_subject_get (theMouse.stimResultsDict)

                    
               
        
        
        
        self.mouse.show()
        thisSubclass = self.__class__.__name__.lstrip('AHF_Stimulator_')
        CAD.Show_ordered_dict (self.expSettings.stimDict, 'Settings for {:s} Stimulator'.format(thisSubclass))
        while True:
            response = input ('change stimulus settings (yes or no)?')
            if response [0] == 'Y' or response [0] == 'y':
                CAD.Edit_dict (self.expSettings.stimDict, '{:s} Stimulator'.format(thisSubclass))
                self.setup ()
            response = input ('run {:s} stimulator as configured (yes or no)?'.format(thisSubclass))
            if response [0] == 'Y' or response [0] == 'y':
                self.run ()
                self.logfile()
                self.mouse.show()
            else:
                break



    def config_user_subject_get(self, starterDict={}):
        print('=============== Default Pull Difficulty Settings ==================')
        toGoalTime = starterDict.get ('toGoalTime', AHF_Stimulator_Lever.defaultToGoalTime)
        response = input('Enter the time the mouse has to get lever into goal area, currently {:.2f}: '.format (toGoalTime))
        if response != '':
            toGoalTime = float (response)

        holdTime = starterDict.get ('holdTime', AHF_Stimulator_Lever.defaultHoldTime)
        response = input('Enter the time the mouse has to hold lever in the goal area, currently {:.2f}: '.format (holdTime))
        if response != '':
            holdTime = float (response)

        goalCenter = starterDict.get ('goalCenter', AHF_Stimulator_Lever.defaultGoalCenter)
        response = input('Enter the center of the goal area (currently {:d}): '.format (goalCenter))
        if response != '':
            goalCenter = int (response)

        goalWidth = starterDict.get ('goalWidth', AHF_Stimulator_Lever.defaultGoalWidth)
        response = input('Enter the width of the goal area (currently {:d}): '.format (goalWidth))
        if response != '':
            goalWidth = int (response)

        starterDict.update({'toGoalTime': toGoalTime, 'holdTime': holdTime, 'goalCenter': goalCenter, 'goalWidth': goalWidth})

        print('=============== Perturbation Settings ==================')
        perturbPercent = starterDict.get ('perturbPercent', AHF_Stimulator_Lever.defaultPerturbPercent)
        response = input('Enter the ratio of trials with perturbations (0.0-1.0) (currently {:.2f}): '.format (perturbPercent))
        if response != '':
            perturbPercent = float (response)

        perturbRampDur = starterDict.get ('perturbRampDur', AHF_Stimulator_Lever.defaultPerturbRampDur)
        response = input('Enter the duration of perturbation ramp (currently {:.2f}): '.format (perturbRampDur))
        if response != '':
            perturbRampDur = float (response)

        perturbStartTime = starterDict.get ('perturbStartTime', AHF_Stimulator_Lever.defaultPerturbStartTime)
        response = input('Enter the time from goal to start of perturbation (currently {:.2f}): '.format (perturbStartTime))
        if response != '':
            perturbStartTime = float (response)

        perturbStartRandom = starterDict.get ('perturbStartRandom', AHF_Stimulator_Lever.defaultPerturbStartRandom)
        response = input('Enter the maximum randomized amount to add/subtract to perturbStartTime (currently {:.2f}): '.format (perturbStartRandom))
        if response != '':
            perturbStartRandom = float (response)

        perturbForceOffset = starterDict.get ('perturbForceOffset', AHF_Stimulator_Lever.defaultPerturbForceOffset)
        response = input('Enter the added force on lever during a perturbation (currently {:d}): '.format (perturbForceOffset))
        if response != '':
            perturbForceOffset = int (response)

        perturbForceRandom = starterDict.get ('perturbForceRandom', AHF_Stimulator_Lever.defaultPerturbForceRandom)
        response = input('Enter the randomized force range on lever during a perturbation (currently {:d}): '.format (perturbForceRandom))
        if response != '':
            perturbForceRandom = int (response)
        starterDict.update({'perturbPercent': perturbPercent, 'perturbRampDur': perturbRampDur, 'perturbStartTime': perturbStartTime, 'perturbStartRandom': perturbStartRandom})
        starterDict.update({'perturbForceOffset': perturbForceOffset, 'perturbForceRandom': perturbForceRandom})

        print('=============== Training Settings ==================')

        promoteRate = starterDict.get ('promoteRate', AHF_Stimulator_Lever.defaultPromoteRate)
        response = input('Enter the performance rate to exceed to be promoted (currently {:d}): '.format (promoteRate))
        if response != '':
            promoteRate = float (response)

        demoteRate = starterDict.get ('demoteRate', AHF_Stimulator_Lever.defaultDemoteRate)
        response = input('Enter the performance rate below which to be demoted (currently {:d}): '.format (demoteRate))
        if response != '':
            demoteRate = float (response)
        starterDict.update({'trainSize': trainSize, 'promoteRate': promoteRate, 'demoteRate': demoteRate})

        goalTrainOn = starterDict.get ('goalTrainOn', AHF_Stimulator_Lever.defaultGoalTrainOn)
        response = input('Enter whether the goal train is on; bit 0 means training, bit 1 means demotion is not allowed, only promotion to next level (currently {:d}): '.format (goalTrainOn))
        if response != '':
            goalTrainOn = int (response)

        goalStartWidth = starterDict.get ('goalStartWidth', AHF_Stimulator_Lever.defaultGoalStartWidth)
        response = input('Enter starting goal width (currently {:d}): '.format (goalStartWidth))
        if response != '':
            goalStartWidth = int (response)

        goalEndWidth = starterDict.get ('goalEndWidth', AHF_Stimulator_Lever.defaultGoalEndWidth)
        response = input('Enter ending goal width (currently {:d}): '.format (goalEndWidth))
        if response != '':
            goalEndWidth = int (response)

        goalIncr = starterDict.get ('goalIncr', AHF_Stimulator_Lever.defaultGoalIncr)
        response = input('Enter amount hold time increases by, by level (currently {:d}): '.format (goalIncr))
        if response != '':
            goalIncr = int (response)
        starterDict.update({'goalTrainOn': goalTrainOn, 'goalStartWidth': goalStartWidth, 'goalEndWidth': goalEndWidth, 'goalIncr': goalIncr})

        holdTrainOn = starterDict.get ('holdTrainOn', AHF_Stimulator_Lever.defaultHoldsTrainOn)
        response = input('Enter whether the hold train is on; bit 0 means training, bit 1 means demotion is not allowed, only promotion to next level (currently {:d}): '.format (holdTrainOn))
        if response != '':
            holdTrainOn = int (response)

        holdStartTime = starterDict.get ('holdStartTime', AHF_Stimulator_Lever.defaultHoldStartTime)
        response = input('Enter starting hold time (currently {:d}): '.format (holdStartTime))
        if response != '':
            holdStartTime = int (response)

        holdEndTime = starterDict.get ('holdEndTime', AHF_Stimulator_Lever.defaultHoldEndTime)
        response = input('Enter ending hold time (currently {:d}): '.format (holdEndTime))
        if response != '':
            holdEndTime = int (response)

        holdIncr = starterDict.get ('holdIncr', AHF_Stimulator_Lever.defaultHoldIncr)
        response = input('Enter amount goal width decreases by, by level (currently {:d}): '.format (holdIncr))
        if response != '':
            holdIncr = int (response)
        starterDict.update({'holdTrainOn': holdTrainOn, 'holdStartTime': holdStartTime, 'holdEndTime': holdEndTime, 'holdIncr': holdIncr})
        return starterDict

                


    
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
        # make signed word array of position data
        self.posArray = array ('h', [0] * self.posArraySize)
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
