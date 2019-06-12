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
        """
        results tuple defines dictionaries for subjects that our favorite objects will write results to
        for making daily tallies of results
        HeadFixer writes number of headfixes and un-fixes to its dictionary
        rewarder writes number and kind of rewards given to its dictionary
        TagReader writes number of chamber entrances to its dictionary
        Stimulator writes results of whatever it does during a head-fix session
        """
        settingsTuple= ('HeadFixer', 'Rewarder', 'Stimulator')
        """
        settings tuple defines dictionaries for subjects that our favorite objects will read from and write personalized settings
        personal settings should be initialized from settings, or cloned from defaults set by the objects, if new subjects are added
        """

    @abstractmethod
    def get (self, IDnum):
        """
        returns results/settings dictionary for individual in group of subjects based on a ID tag.
        """
        pass

    @abstractmethod
    def check (self, IDnum):
        """
        returns 1 if IDnum is already in subjects, 0 if IDnum is not in subjects but is elgible to be added, returns -1 if IDnum is not elgible to be added
        """
        return -1


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
        returns True if subject was added, false if subject with IDnum already exists in subject pool
        """
        pass

    @abstractmethod
    def get_all (self):
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
        The attributes will be defined by subclass, results provided by stimulator, etc. Returns true if IDNum was found in
        pool, else False
        """


    @abstractmethod
    def subjectSettings(self):
        """
        changes the subject specific parameters that are (usually) independent from basic hardware settings
        e.g. headfix time, headfix tightness, reward size, add or remove a subject to a cage, stimulation specifications,
        task settings
        """
        pass