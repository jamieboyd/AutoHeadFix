#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_Subjects (AHF_Base, metaclass = ABCMeta):
    """
    Base class for experimental subjects. Defines subject attributes. Subjects must be unique for ID attribute
    Subclasses may wish to define an inner class that describes an object for a single experimental subject.
    """


    @abstractmethod
    def setup(self):
        resultsTuple = ('HeadFixer', 'Rewarder', 'Stimulator') # results tuple defines dictionaries for subjects we will read from and write results to
        settingsTuple= ('HeadFixer', 'Rewarder', 'Stimulator') # results tuple defines dictionaries for subjects we will read from and write settings to 

    @abstractmethod
    def get (self, IDnum):
        """
        returns tuple of results dictionary/settings dictionary for individual in group of subjects based on a ID tag.
        """
        pass

    @abstractmethod
    def generator (self):
        """
        Generator function that generates dictionaries of settings for all of the subjects in turn
        """
        pass

    @abstractmethod
    def add (self, IDnum, dataDict):
        """
        Adds a new subject to the pool of subjects, initializing subject fields with data from a dictionary
        returns True if subject was added, false if subjet with IDnum already exists in subject pool
        """
        pass

    @abstractmethod
    def remove (self, IDnum):
        """
        Removes a subject from the pool of subjects, based on IDnumber. Returns true if subject with given OD was
        found and removed, returns false if no subject with IDnum was found in pool of subjects
        """
        pass

    @abstractmethod
    def userEdit (self):
        """
        Allows user interaction to add and remove subjects, maybe print out and edit individual configuration
        """
        pass

    @abstractmethod
    def show (self, IDNum = 0):
        """
        Prints out attributes for subject with given IDNum. If IDNum is 0, prints attributes for all subjects in pool.
        The attributes will be defined by subclass, results provided by stimulator, etc. Retyrns true if IDNum was found in
        pool, else False
        """

    @abstractmethod
    def newSubjectDict (starterDict = {}):
        """
        New dictionary made for each individual mouse, dictionaries for headFixer, rewarder, Stmiulator, and
        tube entries, which are not tracked by stimulator, head fixer, or rewarder
        A separate dictionary tracks individual settings, which over-ride global settings
        """
        resultsDict = {}
        for results in self.resultsTuple:
            resultsDict.update (results, {})
        settingsDict = {}
        for settings in settingsTuple:
            settingsDict.update (settings, {})
        return {'results' : resultsDict, 'settings' : settingsDict}
            

    

    


    
        
