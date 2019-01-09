#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect

class AHF_HeadFixer(metaclass = ABCMeta):
    """
    Base class for all head fix classs. Other head fixers subclass from this, or from one of its subclasses
    boolean for settability of headFixing levels, default is False. Can be used for incremental learning
    """
    hasLevels = False
    

    ##################################################################################
    #abstact methods each headfixer class must implement
    #part 1: three main methods of initing, fixing, and releasing
    @abstractmethod
    def __init__(self, settingsDict):
        """
        hardware initialization of a headFixer, reading data from the task object
        """
        pass

    @abstractmethod
    def setup (self):
        """
        does hardware initialization of a headFixer with (possibly updated) info in self.settingsDict
        """
        pass
        

    @abstractmethod
    def fixMouse(self):
        """
        performs head fixation by energizing a piston, moving a servomotor, etc
        """
        pass
    
    @abstractmethod
    def releaseMouse(self):
        """
        releases mouse from head fixation by relaxing a piston, moving a servomotor, etc
        """
        pass

    ##################################################################################
    #abstact methods each headfixer class must implement
    #part 2: static function for getting ConfigDict from user


    @staticmethod
    @abstractmethod
    def config_user_get ():
        """
        in absence of json configDict, querries user for settings, and returns a dictionary with settings
        """
        pass


    

    ##################################################################################
    #abstract methods each headfixer class must implement
    #part 3: hadware tester function
    @abstractmethod
    def test(self, task):
        """
        Called by hardwaretester, runs a harware test for headFixer, verifying that it works
        gives user a chance to change configuration, and, if changed, saves new configuration info in headFixer dictionary in task
        """
        pass

    ###################################################################################
    # methods a headFixer will implement if it hasLevels
    # we pass the current level of a particular mouse and level up before head fixing
    # we save the returned new value in the mouse object, for next time

    def level_get_start (self):
        return 0
    
    def level_up (self, baseValue):
        return baseValue + 0

    def level_down (self, baseValue):
        return baseVaue - 0

    def level_set_level (self, level):
        pass

    ##################################################################################
    # a simple function to run when run as Main, for all head fixers
    @staticmethod
    def funcForMain ():
        from time import sleep
        from AHF_HeadFixer import AHF_HeadFixer
        from AHF_Task import AHF_Task
        task = AHF_Task(None)
        task.edit()
        task.save()
        headFixer=AHF_HeadFixer.get_class (task.headFixerClass) (task.headFixerDict)
        print ('Released Position')
        headFixer.releaseMouse()
        sleep (1)
        print ('Fixed Position')
        headFixer.fixMouse()
        sleep (1)
        print ('Released Position')
        headFixer.releaseMouse()


if __name__ == "__main__":
    AHF_HeadFixer.funcForMain()

