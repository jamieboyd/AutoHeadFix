#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod
from inspect import isabstract
from os import listdir

import AHF_ClassAndDictUtils as CAD
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse


from time import time, sleep
from datetime import datetime

class AHF_Stimulator (metaclass = ABCMeta):

    """
    Abstract base class for Stimulator methods, as several exist and we may wish to choose between them at run time

    Stimulator does and reward during a head fix task
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.
    """

    @staticmethod
    def get_class(fileName):
        
        """
        static method that imports a module from a fileName (stripped of the .py) and returns the class, or None if module could not be loaded

        Assumes the class is named the same as the module.
        """
        return CAD.Class_from_file('Stimulator', fileName.rstrip('.py').lstrip('AHF_Stimulator_'))


    @staticmethod
    def get_Stimulator_from_user ():
        """
        Static method that trawls through current folder looking for Stimulator class python files from which user chooses one
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_Stimulator_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        Returns: name of the file the user chose, stripped of AHF_Settings and .py
        """
        return CAD.Subclass_from_user(CAD.Class_from_file('Stimulator', ''))


    @staticmethod
    @abstractmethod
    def about():
        return 'a brief description of your stimulator'


    @staticmethod
    @abstractmethod
    def dict_from_user (stimDict = {}):
        """
        static method that querries user to make or edit a dictionary that holds settings for a stimulator
        subclassses must provide this
        """
        return stimDict
    
    
    def __init__ (self, cageSettings, expSettings, rewarder, lickDetector):
        """
        The Stimulator class is inited with references to cageSettings, experiment settings (includes stimDict)
        and references to the rewarder and lickDetector objects. references are copied to instance variables
        and the setup function is run. Subclasses will probably not need to overwrite this function, but will
        need to provide their own setup function
        """
        self.cageSettings = cageSettings
        self.expSettings = expSettings
        self.rewarder = rewarder
        self.lickDetector = lickDetector
        if not hasattr(expSettings, 'stimDict'):
            setattr(expSettings, 'stimDict', self.dict_from_user ({}))
        self.mouse = None
        self.setup()
        

    @abstractmethod
    def setup (self):
        """
        abstract method subclasses must provide to init any hardware and other resources
        """
        pass
    

    @abstractmethod
    def configStim (self, mouse):
        """
        Called before running each head fix trial, stimulator decides what to do and configures itself

        You may wish to different things for different mice, and to store data about stim presentations in the mouse object
        :returns: a short string representing stim configuration, used to generate movie file name
        :param mouse: the object representing the mouse that is currently head-fixed
        """
        return 'stim'


    @abstractmethod
    def run (self):
        """
        Called at start of each head fix. 
        """
        pass


    @abstractmethod
    def tester (self):
        """
        Tester function called from the hardwareTester. Includes Stimulator
        specific hardware tester.
        """
        pass

    

    
    def logFile (self):
        """
        Called after each head fix, prints more detailed text to the log file, perhaps a line for each event

        You may wish to use the same format as writeToLogFile function in __main__.py

        Or you may wish to log from the run method
        """
        pass
    
    def nextDay (self, mice):
        """
        Called when the next day starts, Stimulator can zero values that are tallied daily
        :param mice: so stimulator can modify results dictionary for all the mice
        """
        pass



    def quitting (self):
        """
            Called before AutoHeadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        pass


