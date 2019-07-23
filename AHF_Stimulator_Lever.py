 #! /usr/bin/python
#-*-coding: utf-8 -*

import ptLeverThread
from array import array
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
import time
from random import random
from PTLeverThread import PTLeverThread
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

    def config_subject_get (self, starterDict = {}):
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

        promoteRate = starterDict.get ('promoteRate', AHF_Stimulator_Lever.defaultPromoteRate)
        demoteRate = starterDict.get ('demoteRate', AHF_Stimulator_Lever.defaultDemoteRate)
        starterDict.update({'promoteRate': promoteRate, 'demoteRate': demoteRate})

        goalTrainOn = starterDict.get ('goalTrainOn', AHF_Stimulator_Lever.defaultGoalTrainOn)
        goalStartWidth = starterDict.get ('goalStartWidth', AHF_Stimulator_Lever.defaultGoalStartWidth)
        goalEndWidth = starterDict.get ('goalEndWidth', AHF_Stimulator_Lever.defaultGoalEndWidth)
        goalIncr = starterDict.get ('goalIncr', AHF_Stimulator_Lever.defaultGoalIncr)
        starterDict.update({'goalTrainOn': goalTrainOn, 'goalStartWidth': goalStartWidth, 'goalEndWidth': goalEndWidth, 'goalIncr': goalIncr})

        holdTrainOn = starterDict.get ('holdTrainOn', AHF_Stimulator_Lever.defaultHoldTrainOn)
        holdStartTime = starterDict.get ('holdStartTime', AHF_Stimulator_Lever.defaultHoldStartTime)
        holdEndTime = starterDict.get ('holdEndTime', AHF_Stimulator_Lever.defaultHoldEndTime)
        holdIncr = starterDict.get ('holdIncr', AHF_Stimulator_Lever.defaultHoldIncr)
        starterDict.update({'holdTrainOn': holdTrainOn, 'holdStartTime': holdStartTime, 'holdEndTime': holdEndTime, 'holdIncr': holdIncr})
        return starterDict

    def setup (self):
        self.recordingTime = self.settingsDict.get('recordingTime')
        self.leverIsReversed = self.settingsDict.get('leverIsReversed')
        self.goalCuePin = self.settingsDict.get('goalCuePin')
        self.goalCueFreq = self.settingsDict.get('goalCueFreq')
        self.constForce = self.settingsDict.get('constForce')
        self.motorEnable = self.settingsDict.get('motorEnable')
        self.motorIsReversed = self.settingsDict.get('motorIsReversed')
        self.motorDir = self.settingsDict.get('motorDir')
        self.trainSize = self.settingsDict.get('trainSize')
        self.trialIsCued = self.settingsDict.get('trialIsCued')
        if self.trialIsCued:
            self.startCuePin = self.settingsDict.get('startCuePin')
            self.startCueFreq = self.settingsDict.get('startCueFreq')
            self.startCueDur = self.settingsDict.get('startCueDur')
            self.trialTimeout = self.settingsDict.get('trialTimeout')
            self.leverController = PTLeverThread(self.recordingTime, self.trialIsCued,
                self.trialTimeout, self.leverIsReversed, self.goalCuePin, self.goalCueFreq,
                self.motorEnable, self.motorDir, self.motorIsReversed, self.startCuePin, self.startCueDur, self.startCueFreq, self.trialTimeout)
            self.leverController.setCued(True)
        else:
            self.prePullTime = self.settingsDict.get('prePullTime')
            self.leverController = PTLeverThread(self.recordingTime, self.trialIsCued,
            self.prePullTime, self.leverIsReversed, self.goalCuePin, self.goalCueFreq,
                self.motorEnable, self.motorDir, self.motorIsReversed)
        self.leverController.setConstForce(self.constForce)
        self.task.DataLogger.startTracking('lever_pull', 'outcome', 'buffer', self.trainSize)

    def run (self, level = -1, settingsDict= {}, resultsDict= {}):
        super().run()
        print("running")
        self.leverController.setMotorEnable(1)
        time.sleep(0.2)
        self.leverController.applyConstForce()
        self.leverController.setMotorEnable(0)
        time.sleep(0.2)
        self.leverController.setMotorEnable(1)
        if self.task.tag <= 0:
            return
        mouseDict = self.task.Subjects.get(self.task.tag).get("Stimulator")
        self.leverController.setTimeToGoal(mouseDict.get("toGoalTime"))
        endTime = time.time() + self.task.Subjects.get(self.task.tag).get("HeadFixer", {}).get('headFixTime')
        while time.time() < endTime:
            print("trial")
            if not self.running:
                break
            goalWidth = mouseDict.get("goalWidth")
            goalCenter = mouseDict.get("goalCenter")
            goalBottom = int(goalCenter - goalWidth/2)
            goalTop = int(goalCenter + goalWidth/2)
            self.leverController.setHoldParams(goalBottom, goalTop, mouseDict.get("holdTime"))
            if random() > 1.0 - mouseDict.get("perturbPercent"):
                self.leverController.setPerturbTransTime(mouseDict.get("perturbRampDur"))
                self.leverController.setPerturbForce(mouseDict.get("perturbForceOffset") + (random() -0.5)*mouseDict.get("perturbForceRandom"))
                self.leverController.setPerturbStartTime(mouseDict.get("perturbStartTime") + (random() -0.5)*mouseDict.get("perturbStartRandom"))
            else:
                self.leverController.setPerturbOff()
            self.leverController.startTrial()
            resultTuple = self.leverController.checkTrial()
            outcome = 0
            if resultTuple[1] >= 1:
                outcome = 1
                self.task.Rewarder.giveReward('task')
            if self.trialIsCued:
                self.task.DataLogger.writeToLogFile(self.task.tag, "lever_pull", {'outcome': outcome ,'positions': self.leverController.posBuffer}, time.time())
            else:
                positions = self.leverController.posBuffer
                circularEnd = self.prePullTime*self.leverController.LEVER_FREQ
                goalPosition = resultTuple[2]
                positions = positions[goalPosition:] + positions[:goalPosition]
                self.task.DataLogger.writeToLogFile(self.task.tag, "lever_pull", {'outcome': outcome ,'positions': self.leverController.posBuffer}, time.time())
            history = self.task.DataLogger.getTrackedEvent(self.task.tag, 'lever_pull', 'outcome')
            average = 0
#            self.leverController.zeroLever(1, False)
            if history is None:
                history = []
            for outcome in history:
                average += outcome
            average /= self.trainSize
            if average > mouseDict.get('promoteRate'):
                print("Promotion")
                self.task.DataLogger.clearTrackedValues(self.task.tag, 'lever_pull', 'outcome')
                if mouseDict.get('goalTrainOn'):
                    newWidth = mouseDict.get('goalWidth') - mouseDict.get('goalIncr')
                    if newWidth >= mouseDict.get('goalEndWidth'):
                        mouseDict.update({'goalWidth': newWidth})
                if mouseDict.get('holdTrainOn'):
                    newTime = mouseDict.get('holdTime') + mouseDict.get('holdIncr')
                    if newTime <= mouseDict.get('holdEndTime'):
                        mouseDict.update({'hold': newTime})
            elif len(history) == self.trainSize and  average < mouseDict.get('demoteRate'):
                print("demotion")
                self.task.DataLogger.clearTrackedValues(self.task.tag, 'lever_pull', 'outcome')
                if mouseDict.get('goalTrainOn'):
                    newWidth = mouseDict.get('goalWidth') + mouseDict.get('goalIncr')
                    if newWidth <= mouseDict.get('goalStartWidth'):
                        mouseDict.update({'goalWidth': newWidth})
                if mouseDict.get('holdTrainOn'):
                    newTime = mouseDict.get('holdTime') - mouseDict.get('holdIncr')
                    if newTime >= mouseDict.get('holdStartTime'):
                        mouseDict.update({'hold': newTime})

            #Do something
    def quitting (self):
        """
            Called before AutoHEadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        pass                

    def setdown (self):
        print ('Withhold stimulator set down')

    def hardwareTest (self):
        # TODO: Test this
        pass

    #  @staticmethod
    # def dict_from_user (stimDict):
    #     if not 'dataSaveFolder' in stimDict:
    #         stimDict.update ({'dataSaveFolder' : '/home/pi/Documents/'})
    #
    #     if not 'decoderReversed' in stimDict:
    #         stimDict.update ({'decoderReversed' : False})
    #     if not 'motorPresent' in stimDict:
    #         stimDict.update ({'motorPresent' : True})
    #     if not 'motorHasDirection' in stimDict:
    #         stimDict.update ({'motorHasDirection' : True})
    #     if not 'motorDirectionPin' in stimDict:
    #         stimDict.update ({'motorDirectionPin' : 18})
    #     if not 'startCuePin' in stimDict:
    #         stimDict.update ({'startCuePin' : 17})
    #     return super(AHF_Stimulator_Lever, AHF_Stimulator_Lever).dict_from_user (stimDict)
