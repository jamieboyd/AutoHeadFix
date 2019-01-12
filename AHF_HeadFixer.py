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
    
    @staticmethod
    @abstractmethod
    def about():
        return ''
    
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
        return {}



    ##################################################################################
    #abstract methods each headfixer class must implement
    #part 3: hadware tester function
    @abstractmethod
    def hardwareTest (self, headFixDict):
        pass

    ###################################################################################
    # method a headFixer will implement if it hasLevels,
    def level_set_level (self, level):
        pass


