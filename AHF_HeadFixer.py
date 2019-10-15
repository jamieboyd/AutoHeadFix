#! /usr/bin/python3
#-*-coding: utf-8 -*-
from time import time, sleep
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base
import AHF_Task
from random import random
class AHF_HeadFixer(AHF_Base, metaclass= ABCMeta):
    """
    Base class for all head fix classs. Other head fixers subclass from this, or from one of its subclasses
    boolean for settability of headFixing levels, default is False. Can be used for incremental learning
    """
    hasLevels = False
    isChecking = False
    defaultPropHeadFix = 0.75
    defaultSkeddadleTime = 5
    defaultHeadFixTime = 40

    @staticmethod
    @abstractmethod
    def config_user_get(starterDict = {}):
        skeddadleTime = starterDict.get('skeddadleTime', AHF_HeadFixer.defaultSkeddadleTime)
        response = input('Enter time, in seconds, for mouse to get head off the contacts when session ends, currently {:.2f}: '.format(skeddadleTime))
        if response != '':
            skeddadleTime = float(skeddadleTime)
        starterDict.update({'skeddadleTime' : skeddadleTime})
        return starterDict

    @abstractmethod
    def config_user_subject_get(self,starterDict = {}):
        headFixTime = starterDict.get('headFixTime',AHF_HeadFixer.defaultHeadFixTime)
        tempInput = input('Set head fixing time,  currently {0}: '.format(headFixTime))
        if tempInput != '':
            headFixTime = float(tempInput)
        starterDict.update({'headFixTime' : headFixTime})
        propHeadFix = starterDict.get('propHeadFix', AHF_HeadFixer.defaultPropHeadFix)
        response = input(
            'Enter proportion(0 to 1) of trials that are head-fixed, currently {:.2f}: '.format(propHeadFix))
        if response != '':
            propHeadFix = float(response)
        starterDict.update({'propHeadFix': propHeadFix})
        return starterDict

    @abstractmethod
    def config_subject_get(self, starterDict={}):
        headFixTime = starterDict.get('headFixTime',AHF_HeadFixer.defaultHeadFixTime)
        starterDict.update({'headFixTime' : headFixTime})
        propHeadFix = starterDict.get('propHeadFix', AHF_HeadFixer.defaultPropHeadFix)
        starterDict.update({'propHeadFix': propHeadFix})
        return starterDict

    def setup(self):
        """
        gets settings from dict, not @abstract because this may be all you nees, as for HeadFixer_NoFix
        """
        self.propHeadFix = self.settingsDict.get('propHeadFix')
        self.isChecking = False
        self.skeddadleTime = self.settingsDict.get('skeddadleTime')

    def newResultsDict(self, starterDict = {}):
        """
        Returns a dictionary counting number of head fixes, subclasses could track more levels of head fixing, e.g.
        """
        starterDict.update({'headFixes' : 0, 'unFixes' : 0})
        return starterDict


    def clearResultsDict(self, resultsDict):
        resultsDict.update({'headFixes' : 0, 'unFixes' : 0})


    def newSettingsDict(self,starterDict = {}):
        starterDict.update({'propHeadFix' : self.propHeadFix})
        return starterDict


    @abstractmethod
    def fixMouse(self, thisTag, resultsDict = {}, settingsDict = {}):
        """
        performs head fixation by energizing a piston, moving a servomotor, etc
        returns True if successful, else false.
        """
        pass


    @abstractmethod
    def releaseMouse(self, thisTag, resultsDict = {}, settingsDict = {}):
        """
        releases mouse from head fixation by relaxing a piston, moving a servomotor, etc
        """
        self.task.fixed = False
        self.task.fixAgainTime = time() + self.skeddadleTime
        self.task.lastFixedTag = thisTag


    @staticmethod
    def isFixedCheck():
        AHF_HeadFixer.isChecking = True
        mouseDict = AHF_Task.gTask.Subjects.get(AHF_Task.gTask.tag)
        if mouseDict is None:
            AHF_HeadFixer.isChecking = False
            return
        lastRewardTime = time()
        rewardGiven = False
        while AHF_Task.gTask.contact:
            try:
                sleep(0.05)
                if time() - lastRewardTime >= mouseDict.get("Rewarder").get("breakBeamDelay"):
                    if AHF_Task.gTask.Rewarder.giveRewardCM("breakBeam") > 0:
                        rewardGiven = True
                        lastRewardTime = time()
                if rewardGiven:
                    mouseDict.get("Rewarder").update({"lastBreakBeamTime": time()})
            except Exception as e:
                AHF_HeadFixer.isChecking = False
                break
        AHF_Task.gTask.Stimulator.stop()
        AHF_HeadFixer.isChecking = False

    def waitForMouse(self, thisTag):
        """
        Utility function for head fix subclasses
        Waits for a mouse to either make contact or leave the chamber
        """

        if self.task.lastFixedTag == thisTag:
            # wait on contact checking if skeddadle time is in effect
            while self.task.tag == thisTag and time() < self.task.fixAgainTime:
                sleep(0.05)
        # wait for contact check or mouse leaving chamber
        while self.task.tag == thisTag and not self.task.contact:
            sleep(0.05)
        return self.task.contact # made contact or left chamber


    def hasMouseLog(self, hasContact, isFixed, thisTag, resultsDict):
        """
        Utility function for head fix subclasses
        Run after head fixing to update common results
        """
        if isFixed:
            if hasContact:
                result = 'check+'
            else:
                result = 'check-'
        else:
            result = 'unfixed'
        fixTime = time()
        self.task.DataLogger.writeToLogFile(thisTag, 'Fix', {'result' : result}, fixTime)
        self.task.lastFixedTime = fixTime
        if hasContact:
            if isFixed:
                newFixes = resultsDict.get('headFixes', 0) + 1
                resultsDict.update({'headFixes' : newFixes})
            else:
                newUnFixes = resultsDict.get('unFixes', 0) + 1
                resultsDict.update({'unFixes' : newUnFixes})


    def hardwareTest(self):
        print(self.__class__.about())
        print('Head Fixer head-fixing for 2 sec')
        self.fixMouse(0, {},{})
        sleep(2)
        self.releaseMouse(0, {},{})
        inputStr=input('Head-Fixer released.\nDo you want to change the Head-Fixer settings?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.setdown()
            self.settingsDict = self.config_user_get(self.settingsDict)
            self.setup()

"""

                thisMouse.currentEntrancesWithNoHeadFix += 1
                thisMouse.currentContinuousHeadFixes = 0
                checkUpLevel(thisMouse, expSettings, stimulator)
                checkDownLevel(thisMouse, expSettings, stimulator)


def checkUpLevel(thisMouse, expSettings, stimulator):
    # Do not do anything to the mouse's level if its not allowed to be head fixed
    if not thisMouse.allowHeadFixation:
        thisMouse.currentContinuousHeadFixes = 0
        thisMouse.currentMultipleHeadFixes = 0
        return

    #CHF = Level change due to continuous head fixes.
    if thisMouse.currentContinuousHeadFixes >= expSettings.continuousHeadFixesForLevelUp and thisMouse.headFixationType < 8 and thisMouse.headFixationType > 1:
        thisMouse.headFixationType += 1
        print("Mouse ", thisMouse.tag, " was leveled up to level(CHF): ", thisMouse.headFixationType)
        log_str = "lvlCHF:" + str(thisMouse.headFixationType-1) + "->" + str(thisMouse.headFixationType)
        writeToLogFile(expSettings.logFP, thisMouse, log_str)
        # We reset both to avoid double bias.
        thisMouse.currentContinuousHeadFixes = 0
        thisMouse.currentMultipleHeadFixes = 0

        if thisMouse.headFixationType == 8:
            thisMouse.timeMaxLevelObtained = time()

#MHF = Level change due to multiple head fixes.
elif thisMouse.currentMultipleHeadFixes >= expSettings.multipleHeadFixesForLevelUp and thisMouse.headFixationType < 8 and thisMouse.headFixationType > 1:
    thisMouse.headFixationType += 1
        print("Mouse ", thisMouse.tag, " was leveled up to level(MHF): ", thisMouse.headFixationType)
        log_str = "lvlMHF:" + str(thisMouse.headFixationType-1) + "->" + str(thisMouse.headFixationType)
        writeToLogFile(expSettings.logFP, thisMouse, log_str)


        # We reset both to avoid double bias.
        thisMouse.currentContinuousHeadFixes = 0
        thisMouse.currentMultipleHeadFixes = 0

        if thisMouse.headFixationType == 8:
            thisMouse.timeMaxLevelObtained = time()
# Max level of the task start increasing trial length instead.
# ITR = Increase task rewards
elif thisMouse.timeMaxLevelObtained is not None:
    if thisMouse.headFixationType == 8 and(time()-thisMouse.timeMaxLevelObtained) >= expSettings.timeToBeginIncreasingTrialLength:
        if((thisMouse.currentContinuousHeadFixes >= expSettings.continuousHeadFixesForLevelUp) or
           (thisMouse.currentMultipleHeadFixes >= expSettings.multipleHeadFixesForLevelUp) and
           (stimulator.nRewards*expSettings.taskRewardTime <= expSettings.maxTimePerTrial)):

            thisMouse.extraTaskRewards += 1
                log_str = "lvlITR:" + str(thisMouse.extraTaskRewards-1) + "->" + str(thisMouse.extraTaskRewards)
                writeToLogFile(expSettings.logFP, thisMouse, log_str)
                stimulator.nRewards = stimulator.baseRewards + thisMouse.extraTaskRewards


                # We reset both to avoid double bias.
                thisMouse.currentContinuousHeadFixes = 0
                thisMouse.currentMultipleHeadFixes = 0


def checkDownLevel(thisMouse, expSettings, stimulator):
    # Do not do anything to the mouse's level if its not allowed to be head fixed
    if not thisMouse.allowHeadFixation:
        thisMouse.currentEntrancesWithNoHeadFix = 0
        return
    #EHF = Level change due to many entrances.
    if thisMouse.currentEntrancesWithNoHeadFix >= expSettings.entrancesWithNoHeadFixForLevelDown and thisMouse.headFixationType > 1 and thisMouse.extraTaskRewards == 0:
        thisMouse.headFixationType -= 1
        print("Mouse ", thisMouse.tag, " was leveled down to level(EHF): ", thisMouse.headFixationType)
        log_str = "lvlEHF:" + str(thisMouse.headFixationType+1) + "->" + str(thisMouse.headFixationType)
        writeToLogFile(expSettings.logFP, thisMouse, log_str)

        #Reset
        thisMouse.currentEntrancesWithNoHeadFix = 0

    # Max level of the task modify trial length instead.
    # DTR = decrease task rewards
    if thisMouse.timeMaxLevelObtained is not None:
        if thisMouse.headFixationType == 7 and(time()-thisMouse.timeMaxLevelObtained) >= expSettings.timeToBeginIncreasingTrialLength:
            if(thisMouse.currentEntrancesWithNoHeadFix >= expSettings.entrancesWithNoHeadFixForLevelDown and
                thisMouse.extraTaskRewards > 0):

                thisMouse.extraTaskRewards -= 1
                log_str = "lvlDTR:" + str(thisMouse.extraTaskRewards+1) + "->" + str(thisMouse.extraTaskRewards)
                writeToLogFile(expSettings.logFP, thisMouse, log_str)
                stimulator.nRewards = stimulator.baseRewards + thisMouse.extraTaskRewards

                #Reset
                thisMouse.currentEntrancesWithNoHeadFix = 0
"""
