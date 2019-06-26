#! /usr/bin/python3
#-*-coding: utf-8 -*-
"""
AHF_Base.py
================================================
The base upon which everything else is built
"""
from abc import ABCMeta, abstractmethod

#This creates a cyclic import - doesn't seem to be a problem on it's own, but
#it is creating problems in debugging.
#import AHF_ClassAndDictUtils as CAD

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

    @staticmethod
    def subject_user_get(starterDict = {}):
        """
        :returns: dict -- an updated dictionary after asking the user for subject related and maybe individualized parameters
        """
        return starterDict



    def __init__(self, taskP, settingsDictP):
        """
        Initialization of a subclass object may be just making a link to the settings dict and running setup
        so this does not need to be an abstract function - your class can use as is
        __init__ will be passed both the settings dict andthe entire Task including the settings dict
        Class names need to start with AHF_ and the dictionary must follow convention, named for the class with 'Dict' appended.

        Args:
            taskP (pointer): Task Pointer - points to the global Task object
            settingsDictP (pointer): Points to the global settings dictionary

        """
        self.task=taskP
        self.settingsDict = settingsDictP
        self.setup()


    @abstractmethod
    def setup (self):
        """
        does hardware initialization with (possibly updated) info in self.settingsDict
        Run by __init__, or can be run  separately after editing the settingsDict

        :returns: bool -- the truth that setup completed without errors
        """
        return True

    @abstractmethod
    def setdown (self):
        """
        oppposite of setup. Releases any hardware resouces. can be run before editing settings so GPIO
        pins can be reused, for example. This strategy should be used in hardwareTest method.
        """
        pass

    def __del__ (self):
        """
        For clean up purposes, releases hardware resources with setdown method
        """
        self.setdown()


    @abstractmethod
    def hardwareTest (self):
        """
        Tests functionality, gives user a chance to change settings.
        :Returns: bool -- True if any settings have changed
        """
        return False
