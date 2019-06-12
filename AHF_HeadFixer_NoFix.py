#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
from time import sleep

class AHF_HeadFixer_NoFix (AHF_HeadFixer):
    """
    Head Fixer that only checks for contact, does not implement a
    head-fixing mechanism
    """
    hasLevels = False
    defaultSkeddadleTime = 0.5
    
    @staticmethod
    def about():
        return 'Head Fixer that only checks for contact, does not implement a head-fixing mechanism'

    @staticmethod
    def config_user_get (starterDict = {}):
        """
        Querries user returns dictionary 
        """
        skeddadleTime = starterDict.get ('skeddadleTime', AHF_HeadFixer.defaultSkeddadleTime)
        response = input ('Enter time, in seconds, for mouse to get head off the contacts when session ends, currently {:.2f}: '.format(skeddadleTime))
        if response != '':
            skeddadleTime = float (skeddadleTime)
        starterDict.update ({'propHeadFix' : 0, 'skeddadleTime' : skeddadleTime})
        return starterDict

    def config_subject_get (self, starterDict = {}):
        return super().config_subject_get(self, starterDict)

    def config_user_subject_get  (self, starterDict = {}):
        return super().config_user_subject_get(self, starterDict)

    def setdown(self):
        pass

    def fixMouse(self, resultsDict = {}, settingsDict = {}):
        """
        Just does contact check with super(), does not fix
        """
        return super().fixMouse (resultsDict, settingsDict)


    def releaseMouse(self, resultsDict = {}, settingsDict = {}):
        super().releaseMouse (resultsDict, settingsDict)

    def hardwareTest (self):
        print (self.__class__.about())
        print ('There is no hardware test for HeadFixer_NoFix')

    
    
