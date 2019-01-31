#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class AHF_BrainLight (metaclass = ABCMeta):

    @staticmethod
    def about():
        return 'A description of your brain illumination class goes here'
    

    @staticmethod
    @abstractmethod
    def config_user_get (starterDict = {}):
        """
        in absence of json configDict, querries user for settings, and returns a dictionary with settings
        """
        return {}

    @abstractmethod
    def __init__(self, settingsDict):
        """
        hardware initialization of a brain lighter, reading data from a settings dictionary
        """
        pass

    @abstractmethod
    def setup (self):
        """
        does hardware initialization of a headFixer with (possibly updated) info in self.settingsDict
        """
        pass


    @abstractmethod
    def hardwareTest (self):
        pass



    @abstractmethod
    def onForStim (self):
        pass


    @abstractmethod
    def offForStim (self):
        pass
    
