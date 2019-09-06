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

    def config_subject_get(self, starterDict = {}):
        return super().config_subject_get(starterDict)

    def config_user_subject_get(self, starterDict = {}):
        return super().config_user_subject_get(starterDict)

    @staticmethod
    def isFixedCheck():
        AHF_HeadFixer_NoFix.isChecking = True
        mouseDict = AHF_Task.gTask.Subjects.get(AHF_Task.gTask.tag)
        if mouseDict is None:
            AHF_HeadFixer_NoFix.isChecking = False
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
                AHF_HeadFixer_NoFix.isChecking = False
                break
        AHF_Task.gTask.Stimulator.stop()
        AHF_HeadFixer_NoFix.isChecking = False

    def setup(self):
        self.isChecking = False
        self.task.isFixTrial = False
        super().setup()

    def setdown(self):
        pass

    def fixMouse(self, tag, resultsDict = {}, settingsDict = {}):
        """
        Just does contact check with super(), does not fix
        """
        if self.task.contact and not AHF_HeadFixer_NoFix.isChecking:
            start_new_thread(self.isFixedCheck,())
            return True
        return False



    def releaseMouse(self, tag, resultsDict = {}, settingsDict = {}):
        super().releaseMouse(tag, resultsDict, settingsDict)

    def hardwareTest(self):
        print(self.__class__.about())
        print('There is no hardware test for HeadFixer_NoFix')
