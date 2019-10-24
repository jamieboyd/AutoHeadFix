#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
import AHF_Task
from time import sleep, time
from _thread import start_new_thread

class AHF_HeadFixer_NoFix(AHF_HeadFixer):
    """
    Head Fixer that only checks for contact, does not implement a
    head-fixing mechanism
    """
    hasLevels = False
    defaultSkeddadleTime = 0.5
    isChecking = False
    @staticmethod
    def about():
        return 'Head Fixer that only checks for contact, does not implement a head-fixing mechanism'

    @staticmethod
    def config_user_get(starterDict = {}):
        """
        Querries user returns dictionary
        """
        skeddadleTime = starterDict.get('skeddadleTime', AHF_HeadFixer.defaultSkeddadleTime)
        response = input('Enter time, in seconds, for mouse to get head off the contacts when session ends, currently {:.2f}: '.format(skeddadleTime))
        if response != '':
            skeddadleTime = float(skeddadleTime)
        starterDict.update({'propHeadFix' : 0, 'skeddadleTime' : skeddadleTime})
        return starterDict

    def config_user_subject_get(self, starterDict = {}):
        headFixTime = starterDict.get('headFixTime',AHF_HeadFixer.defaultHeadFixTime)
        tempInput = input('Set allowed time in chamber for lick withhold trials,  currently {0}: '.format(headFixTime))
        if tempInput != '':
            headFixTime = float(tempInput)
        starterDict.update({'headFixTime' : headFixTime})
        return starterDict

    def config_subject_get(self, starterDict = {}):
        headFixTime = starterDict.get('headFixTime',AHF_HeadFixer.defaultHeadFixTime)
        starterDict.update({'headFixTime' : headFixTime})
        return starterDict


    def setup(self):
        AHF_HeadFixer.isChecking = False
        self.task.isFixTrial = False
        super().setup()

    def setdown(self):
        pass

    def fixMouse(self, tag, resultsDict = {}, settingsDict = {}):
        """
        Just does contact check with super(), does not fix
        """
        self.hasMouseLog(False, self.task.isFixTrial, tag, resultsDict)
        if self.task.contact and not AHF_HeadFixer.isChecking:
            start_new_thread(self.isFixedCheck,())
            return True
        return False



    def releaseMouse(self, tag, resultsDict = {}, settingsDict = {}):
        super().releaseMouse(tag, resultsDict, settingsDict)

    def hardwareTest(self):
        print(self.__class__.about())
        print('There is no hardware test for HeadFixer_NoFix')
