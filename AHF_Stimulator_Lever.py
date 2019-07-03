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
    defaultConstForce = 1300 # constant force on lever at start of trial that mouse must pull against, as opposed to perturbForce set during a trial a 12 bit value, 0 to 4095
    defaultTrialIsCued = False # True means trials will be started with the start cue; False means mouse starts pulling lever whenever he likes
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
    defaultPerturbStartTime # time from ToGoalTime to start of perturbation
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

    #pathToData_def = '/home/pi/Documents/' # folder where lever pos files will be saved, or maybe just pass the array to the DataLogger

    @staticmethod
    def about():
        return 'As mice hold a lever in a set angular range, Lever stimulator records lever position and puts torque on the lever by calling ptLeverThread C-module.'

    @staticmethod
    def config_user_get (starterDict = {}):
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
        response = input ('Enter the constant force applied to the on lever at the start of a trial, from 0 to 4095 (currently {:d}): '.format (constForce))
        if response != '':
            constForce = int (response)

        trialIsCued = StarterDict.get ('trialIsCued', AHF_Stimulator_Lever.defaultTrialIsCued)
        response = input ('Do the lever pull trials have a start cue? (yes or no, currently {:.str}): '.format ('Yes' if mybool else 'No'))
        if response != '':
            trialIsCued = True if response.lower()[0] == 'y' else False
        starterDict.update({'recordingTime': recordingTime, 'leverIsReversed': leverIsReversed, 'goalCuePin': goalCuePin, 'goalCueFreq': goalCueFreq})
        starterDict.update({'constForce': constForce, 'trialIsCued': trialIsCued})
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
            prePullTime = starterDict.get ('prePullTime', AHF_Stimulus_Lever.defaultPrePullTime)
            response = input ('Enter the duration prior to goal position to be saved, currently {:.2f}: '.format (prePullTime))
            if response != '':
                prePullTime = float (response)
            starterDict.update({'prePullTime': prePullTime})

        return starterDict

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

        trainSize = starterDict.get ('trainSize', AHF_Stimulator_Lever.defaultTrainSize)
        response = input('Enter the number of previous trials to examine when deciding promotion/demotion (currently {:.d}): '.format (trainSize))
        if response != '':
            trainSize = int (response)

        promoteRate = starterDict.get ('promoteRate', AHF_Stimulator_Lever.defaultPromoteRate)
        response = input('Enter the performance rate to exceed to be promoted (currently {:.d}): '.format (promoteRate))
        if response != '':
            promoteRate = float (response)

        demoteRate = starterDict.get ('demoteRate', AHF_Stimulator_Lever.defaultDemoteRate)
        response = input('Enter the performance rate below which to be demoted (currently {:.d}): '.format (demoteRate))
        if response != '':
            demoteRate = float (response)
        starterDict.update({'trainSize': trainSize, 'promoteRate': promoteRate, 'demoteRate': demoteRate})

        goalTrainOn = starterDict.get ('goalTrainOn', AHF_Stimulator_Lever.defaultGoalTrainOn)
        response = input('Enter whether the goal train is on; bit 0 means training, bit 1 means demotion is not allowed, only promotion to next level (currently {:.d}): '.format (goalTrainOn))
        if response != '':
            goalTrainOn = int (response)

        goalStartWidth = starterDict.get ('goalStartWidth', AHF_Stimulator_Lever.defautlGoalStartWidth)
        response = input('Enter starting goal width (currently {:.d}): '.format (goalStartWidth))
        if response != '':
            goalStartWidth = int (response)

        goalEndWidth = starterDict.get ('goalEndWidth', AHF_Stimulator_Lever.defautlGoalEndWidth)
        response = input('Enter ending goal width (currently {:.d}): '.format (goalEndWidth))
        if response != '':
            goalEndWidth = int (response)

        goalIncr = starterDict.get ('goalIncr', AHF_Stimulator_Lever.defautlGoalIncr)
        response = input('Enter amount hold time increases by, by level (currently {:.d}): '.format (goalIncr))
        if response != '':
            goalIncr = int (response)
        starterDict.update({'goalTrainOn': goalTrainOn, 'goalStartWidth': goalStartWidth, 'goalEndWidth': goalEndWidth, 'goalIncr': goalIncr})

        holdTrainOn = starterDict.get ('holdTrainOn', AHF_Stimulator_Lever.defaultHoldsTrainOn)
        response = input('Enter whether the hold train is on; bit 0 means training, bit 1 means demotion is not allowed, only promotion to next level (currently {:.d}): '.format (holdTrainOn))
        if response != '':
            holdTrainOn = int (response)

        holdStartTime = starterDict.get ('holdStartTime', AHF_Stimulator_Lever.defaultHoldStartTime)
        response = input('Enter starting hold time (currently {:.d}): '.format (holdStartTime))
        if response != '':
            holdStartTime = int (response)

        holdEndTime = starterDict.get ('holdEndTime', AHF_Stimulator_Lever.defaultHoldEndTime)
        response = input('Enter ending hold time (currently {:.d}): '.format (holdEndTime))
        if response != '':
            holdEndTime = int (response)

        holdIncr = starterDict.get ('holdIncr', AHF_Stimulator_Lever.defautlHoldIncr)
        response = input('Enter amount goal width decreases by, by level (currently {:.d}): '.format (holdIncr))
        if response != '':
            holdIncr = int (response)
        starterDict.update({'holdTrainOn': holdTrainOn, 'holdStartTime': holdStartTime, 'holdEndTime': holdEndTime, 'holdIncr': holdIncr})
        return starterDict

    def config_subject_get (self):
        toGoalTime = starterDict.get ('toGoalTime', AHF_Stimulator_Lever.defaultToGoalTime)
        holdTime = starterDict.get ('holdTime', AHF_Stimulator_Lever.defaultHoldTime)
        goalCenter = starterDict.get ('goalCenter', AHF_Stimulator_Lever.defaultGoalCenter)
        goalWidth = starterDict.get ('goalWidth', AHF_Stimulator_Lever.defaultGoalWidth)
        starterDict.update({'toGoalTime': toGoalTime, 'holdTime': holdTime, 'goalCenter': goalCenter, 'goalWidth': goalWidth})

        perturbPercent = starterDict.get ('perturbPercent', AHF_Stimulator_Lever.defaultPerturbPercent)
        perturbRampDur = starterDict.get ('perturbRampDur', AHF_Stimulator_Lever.defaultPerturbRampDur)
        perturbStartTime = starterDict.get ('perturbStartTime', AHF_Stimulator_Lever.defaultPerturbStartTime)
        perturbStartRandom = starterDict.get ('perturbStartRandom', AHF_Stimulator_Lever.defaultPerturbStartRandom)
        perturbForceOffset = starterDict.get ('perturbForceOffset', AHF_Stimulator_Lever.defaultPerturbForceOffset)
        perturbForceRandom = starterDict.get ('perturbForceRandom', AHF_Stimulator_Lever.defaultPerturbForceRandom)
        starterDict.update({'perturbPercent': perturbPercent, 'perturbRampDur': perturbRampDur, 'perturbStartTime': perturbStartTime, 'perturbStartRandom': perturbStartRandom})
        starterDict.update({'perturbForceOffset': perturbForceOffset, 'perturbForceRandom': perturbForceRandom})

        trainSize = starterDict.get ('trainSize', AHF_Stimulator_Lever.defaultTrainSize)
        promoteRate = starterDict.get ('promoteRate', AHF_Stimulator_Lever.defaultPromoteRate)
        demoteRate = starterDict.get ('demoteRate', AHF_Stimulator_Lever.defaultDemoteRate)
        starterDict.update({'trainSize': trainSize, 'promoteRate': promoteRate, 'demoteRate': demoteRate})

        goalTrainOn = starterDict.get ('goalTrainOn', AHF_Stimulator_Lever.defaultGoalTrainOn)
        goalStartWidth = starterDict.get ('goalStartWidth', AHF_Stimulator_Lever.defautlGoalStartWidth)
        goalEndWidth = starterDict.get ('goalEndWidth', AHF_Stimulator_Lever.defautlGoalEndWidth)
        goalIncr = starterDict.get ('goalIncr', AHF_Stimulator_Lever.defautlGoalIncr)
        starterDict.update({'goalTrainOn': goalTrainOn, 'goalStartWidth': goalStartWidth, 'goalEndWidth': goalEndWidth, 'goalIncr': goalIncr})

        holdTrainOn = starterDict.get ('holdTrainOn', AHF_Stimulator_Lever.defaultHoldsTrainOn)
        holdStartTime = starterDict.get ('holdStartTime', AHF_Stimulator_Lever.defaultHoldStartTime)
        holdEndTime = starterDict.get ('holdEndTime', AHF_Stimulator_Lever.defaultHoldEndTime)
        holdIncr = starterDict.get ('holdIncr', AHF_Stimulator_Lever.defautlHoldIncr)
        starterDict.update({'holdTrainOn': holdTrainOn, 'holdStartTime': holdStartTime, 'holdEndTime': holdEndTime, 'holdIncr': holdIncr})
        return starterDict

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
