#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod
from inspect import isabstract
from os import listdir

import AHF_ClassAndDictUtils as CAD
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse, Mice


from time import time, sleep
from datetime import datetime

class AHF_Stimulator (metaclass = ABCMeta):
    """
    Abstract base class for Stimulator methods, as several exist and we may wish to choose between them at run time

    All events and their timings in a head fix session, including giving rewards, are controlled by a Stimulator.
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
        Static method that trawls through current folder looking for Stimulator class python files from which the user chooses one
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_Stimulator_' and ending with '.py'
        raises: FileNotFoundError if no stimulator class files found
        returns: name of the file the user chose, stripped of AHF_Settings and .py
        """
        return CAD.Subclass_from_user(CAD.Class_from_file('Stimulator', ''))


    @staticmethod
    @abstractmethod
    def about():
        """
        returns:a brief description of the stimulator class
        """
        return 'a brief description of your stimulator'


    @staticmethod
    @abstractmethod
    def dict_from_user (stimDict = {}):
        """
        static method that querries user to make or edit a dictionary that holds settings for a stimulator
        :param stimDict: a dictionary of settings (may be empty) to edit and return
        """
        return stimDict
    
    
    def __init__ (self, cageSettings, expSettings, rewarder, lickDetector):
        """
        A Stimulator class is inited with references to settings and harware objects, which are copied to instance variables
        
        :param cageSettings: information on GPIO pin numbers, etc.
        :param expSettings: information on task settings and timing, including stimulator dictionary
        :param rewarder: object configured to give water rewards
        :param lickDetector: object configured to detect licks on the water spout
        
        Subclasses will probably not need to overwrite this function, but will need to provide their own setup function
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
        :param mouse: the object representing the mouse that is currently head-fixed
        :returns: a short string representing stim configuration, used to generate movie file name
        """
        return 'stim'


    @abstractmethod
    def run (self):
        """
        Called at start of each head fix. 
        """
        pass


    def tester (self, mice):
        """
        Generic tester function to called from the hardwareTester. Subclasses may override
        
        :param mice: reference to mice so stimulator can edit results/settings dictionary for mice
        makes a sample mouse and calls the run function in a loop, giving option to change settings every time
        """
        
        self.configStim (Mouse (2525, 0,0,0,{}))
        print ('Testing with dummy mouse:')
        self.mouse.show()
        thisSubclass = self.__class__.__name__.lstrip('AHF_Stimulator_')
        CAD.Show_ordered_dict (self.expSettings.stimDict, 'Settings for {:s} Stimulator'.format(thisSubclass))
        while True:
            response = input ('change stimulus settings (yes or no)?')
            if response [0] == 'Y' or response [0] == 'y':
                CAD.Edit_dict (self.expSettings.stimDict, '{:s} Stimulator'.format(thisSubclass))
                self.setup ()
            response = input ('run {:s} stimulator as configured (yes or no)?'.format(thisSubclass))
            if response [0] == 'Y' or response [0] == 'y':
                self.run ()
                self.logfile()
                self.mouse.show()
            else:
                break
        


    def logFile (self):
        """
        Called after each head fix, prints more detailed text to the log file, perhaps a line for each event

        You may wish to use the same format as writeToLogFile function in __main__.py to make analysis more straighforward
        """
        pass


    def nextDay (self, mice):
        """
        Called when the next day starts, Stimulator can, e.g., zero values that are tallied daily
        :param mice: so stimulator can modify results dictionary for all the mice
        """
        pass


    def quitting (self):
        """
        Called before AutoHeadFix exits. Gives stimulator chance to do any needed cleanup

        A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        pass


