#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class AHF_Base (metaclass = ABCMeta):

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


    def __init__(self, settingsDict):
        """
        Initialization of a subclass object may be just making a link to the settings dict
        and running setup so this does not need to be an abtract function
        """
        self.settingsDict = settingsDict
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
        pins can be reused, for example
        """
        pass


    @abstractmethod
    def hardwareTest (self):
        """
        Tests functionality, gives user a chance to change settings
        """
        pass
