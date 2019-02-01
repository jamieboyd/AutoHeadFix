#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

import AHF_ClassAndDictUtils as CAD

class AHF_Base (metaclass = ABCMeta):
    """
    Defines conventions for classes used for accesing hardware and doing subtasks in AutoHeadFix code
    Each class has a static method, config_user_get, to create or edit a settings dictionary, and will be inititialized
    with a settings dictionary. The setup function does hardware initialization, or other inititialization. 
    """
    
    @staticmethod
    @abstractmethod
    def about():
        """
        Returns a brief message describing your sub-class, used when asking user to pick a sub-class of this class
        """
        return 'A description of your sub-class goes here'
    
    @staticmethod
    @abstractmethod
    def config_user_get (starterDict = {}):
        """
        static method that querries user for settings, with default responses from starterDict,
        and returns starterDict with settings as edited by the user.

        """
        return starterDict


    def __init__(self, task):
        """
        Initialization of a subclass object may be just making a link to the settings dict and running setup
        so this does not need to be an abtract function - your class can use as is
        __init__ may be passed just the settings dict or maybe the entire Task including the settings dict
        Class names and need to start with AHF_ and if the whole Task is apssed, the dictionary must
        follow convention, named for the class with 'Dict' appended. 
        
        """
        if hasattr (task, CAD.Super_of_object (self).lstrip('AHF_') + 'Dict'):
            self.settingsDict = getattr (task, CAD.Super_of_object (self).lstrip('AHF_') + 'Dict')
        else:
            self.settingsDict = task
        self.setup ()


    @abstractmethod
    def setup (self):
        """
        does hardware initialization of  with (possibly updated) info in self.settingsDict
        Run by __init__, or can be run  separately after editing the settingsDict
        """
        pass

    @abstractmethod
    def setdown (self):
        """
        oppposite of setup. Releases any hardware resouces. can be run before editing settings so GPIO
        pins can be reused, for example. This strategy should be used in hardwareTest
        """
        pass


    @abstractmethod
    def hardwareTest (self):
        """
        Tests functionality, gives user a chance to change settings
        """
        pass
