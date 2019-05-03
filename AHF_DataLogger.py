#! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base
from AHF_Mouse import Mouse, Mice
class AHF_DataLogger (AHF_Base, metaclass = ABCMeta):
    """
    A Data Logger provides an interface to save task data, and to save
    and load mouse configuration data. This can be either to text files, or to
    a database, or hd5 files, or some combination thereof. The data logger
    should also print status updates to the shell, but these don't need to contain
    as much information. The brain imaging data is saved
    separately, but references to movie files should be saved by data logger.
    Similarly, other binary data (lever positons, anyone?) can be saved separately,
    by the Stimulator class, but binary file/posiiton can be saved as an event.
    """
    TO_SHELL =1
    TO_FILE = 2

    @abstractmethod
    def makeLogFile (self):
        """
        Makes or opens a text log file, or a datbase, or whatever else needs doing. Called once before
        entyering main loop of program. DataLogger may make a new file every day in NewDay function, if desired
        """
        pass

    @abstractmethod
    def writeToLogFile(self, tag, eventKind, eventDict, timeStamp, toShellOrFile):
        """
        The original standard text file method was 4 tab-separated columns, mouse tag, or 0
        if no single tag was applicaple, unix time stamp, ISO formatted time, and event. Event
        could be anything. Now, every event has a kind, and every kind of event defines a
        dictionary. Main program calls writeToLogFile, as well as the Stimulator object
        For text based methods, event should be a dictionary for more complicated stimulator
        results, so an event can be more easily parsed during data analysis.
        """
        pass


    @abstractmethod
    def newDay (self, mice):
        """
        At the start of a new day, it was customary for the text-based data logging to start new text files,
        and to make a precis of the day's results into a a separate text file for easy human reading.
        This "quickStats" file should contain info for each mouse with rewards, head fixes,
        or tasks, and other Stimulator specific data, which Stimulator object will provide for each mouse
        just call the Stimulator class functions for each mouse to get a dictionary of results
        """
        pass

    @abstractmethod
    def configGenerator (self):
        """
        generates configuration data for each subject as (IDtag, dictionary) tuples from some kind of permanent storage
        such as a JSON file, or a database. Will be called when program is started, or restarted and settings
        need to be reloaded.
        """

    @abstractmethod
    def getConfigData (self, tag):
        """
        returns a dictionary of data that was saved for this reference tag, in some permanent storage such as a JSON file
        Will be called when program is started, or restarted and settings need to be reloaded
        """
        pass


    @abstractmethod
    def storeConfig (self, tag, dictionary):
        """
        Stores configuration data, given as an IDtag, and dictionary for that tag, in some more permanent storage
        as a JSON text file, or a database or hd5 file, so it can be later retrived by IDtag
        """
        pass
