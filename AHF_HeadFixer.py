#! /usr/bin/python3
#-*-coding: utf-8 -*-
from time import sleep
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_HeadFixer(AHF_Base, metaclass= ABCMeta):
    """
    Base class for all head fix classs. Other head fixers subclass from this, or from one of its subclasses
    boolean for settability of headFixing levels, default is False. Can be used for incremental learning
    """
    hasLevels = False


    @abstractmethod
    @staticmethod
    def config_user_get (starterDict = {}):
        propHeadFix = starterDict.get ('propHeadFix', AHF_Subjects_mice.propHeadFixDefault)
        response = input('Enter proportion (0 to 1) of trials that are head-fixed, currently {:.2f}: '.format(propHeadFix))
        if response != '':
            propHeadFix = float (response)
        skeddadleTime = starterDict.get ('skeddadleTime', AHF_Subjects_mice.skeddadleTimeDefault)
        response = input ('Enter time, in seconds, for mouse to get head off the contacts when session ends, currently {:.2f}: '.format(skeddadleTime))
        if response != '':
            skeddadleTime = float (skeddadleTime)
        starterDict.update ({'propHeadFix' : propHeadFix, 'skeddadleTime' : skeddadleTime})
    
    @abstractmethod
    def setup (self):
        super().setup()
        self.propHeadFix = self.settingsDict.get ('propHeadFix')
        self.skeddadleTime = self.settingsDict.get ('skeddadleTime')

    def newResultsDict (self, starterDict = {}):
        """
        Returns a dictionary counting number of head fixes, subclasses could track more levels of head fixing, e.g.
        """
        starterDict.update({'headFixes' : 0, 'Un-headFixes' : 0})
        return starterDict


    def clearResultsDict(self, resultsDict):
        resultsDict.update ({'headFixes' : 0, 'Un-headFixes' : 0})
        

    def newSettingsDict (self,starterDict = {}):
        starterDict.update ({'propHeadFix' : self.propHeadFix})
        return starterDict

    @abstractmethod
    def fixMouse(self, resultsDict = {}, settingsDict = {}):
        """
        performs head fixation by energizing a piston, moving a servomotor, etc
        """
        pass
    
    @abstractmethod
    def releaseMouse(self, resultsDict = {},settingsDict = {}):
        """
        releases mouse from head fixation by relaxing a piston, moving a servomotor, etc
        """
        pass


    def hardwareTest (self):
        print (self.__class__.about())
        print ('Head Fixer head-fixing for 2 sec')
        self.fixMouse()
        sleep (2)
        self.releaseMouse ()
        inputStr=input ('Head-Fixer released.\nDo you want to change the Head-Fixer settings?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.setdown ()
            self.settingsDict = self.config_user_get (self.settingsDict)
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
        print("Mouse ", thisMouse.tag, " was leveled up to level (CHF): ", thisMouse.headFixationType)
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
        print("Mouse ", thisMouse.tag, " was leveled up to level (MHF): ", thisMouse.headFixationType)
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
    if thisMouse.headFixationType == 8 and (time()-thisMouse.timeMaxLevelObtained) >= expSettings.timeToBeginIncreasingTrialLength:
        if ((thisMouse.currentContinuousHeadFixes >= expSettings.continuousHeadFixesForLevelUp) or
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
        print("Mouse ", thisMouse.tag, " was leveled down to level (EHF): ", thisMouse.headFixationType)
        log_str = "lvlEHF:" + str(thisMouse.headFixationType+1) + "->" + str(thisMouse.headFixationType)
        writeToLogFile(expSettings.logFP, thisMouse, log_str)
        
        #Reset
        thisMouse.currentEntrancesWithNoHeadFix = 0
    
    # Max level of the task modify trial length instead.
    # DTR = decrease task rewards
    if thisMouse.timeMaxLevelObtained is not None:
        if thisMouse.headFixationType == 7 and (time()-thisMouse.timeMaxLevelObtained) >= expSettings.timeToBeginIncreasingTrialLength:
            if (thisMouse.currentEntrancesWithNoHeadFix >= expSettings.entrancesWithNoHeadFixForLevelDown and
                thisMouse.extraTaskRewards > 0):
                
                thisMouse.extraTaskRewards -= 1
                log_str = "lvlDTR:" + str(thisMouse.extraTaskRewards+1) + "->" + str(thisMouse.extraTaskRewards)
                writeToLogFile(expSettings.logFP, thisMouse, log_str)
                stimulator.nRewards = stimulator.baseRewards + thisMouse.extraTaskRewards
                
                #Reset
                thisMouse.currentEntrancesWithNoHeadFix = 0
"""
