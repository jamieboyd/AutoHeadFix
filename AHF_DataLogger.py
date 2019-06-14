 #! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base
from AHF_Mouse import Mouse, Mice
from collections import deque
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
    trackingDict = {}
    BUFFER_SIZE = 25

    @abstractmethod
    def makeLogFile (self):
        """
        Makes or opens a text log file, or a datbase, or whatever else needs doing. Called once before
        entering main loop of program. DataLogger may make a new file every day in NewDay function, if desired
        """
        pass

    @abstractmethod
    def readFromLogFile(self, index):
        """
        Reads the log statement *index* lines prior to the current line.
        Returns the event and associated dictionary in a tuple.
        """
        pass

    def startTracking(self, eventKind, dictKey, trackingType, size = 0):
        """
        Begins tracking of the specified key for the specified event.
        Tracks as a circular buffer or daily totals.
        """
        self.trackingDict.update({eventKind: {dictKey: {"type": trackingType, "values": {}, "size": size}}})

    def getTrackedEvent(self, tag, eventKind, dictKey):
        """
        Returns the current value for the specified mouse, event, and key.
        """
        try:
            return self.trackingDict.get(eventKind).get(dictKey).get("values").get(tag)
        except Exception as e:
            return None

    def stopTracking(self, eventKind, dictKey):
        """
        Halts previously started tracking.
        """
        try:
            type = self.trackingDict.get(eventKind).get(dictKey).get("type")
            self.trackingDict.get(eventKind).get(dictKey).update({"type": type + "Stopped"})
        except Exception as e:
            pass

    def resumeTracking(self, eventKind, dictKey):
        """
        Resumes previously started tracking.
        """
        try:
            type = self.trackingDict.get(eventKind).get(dictKey).get("type")
            if type[-7:] is "Stopped":
                self.trackingDict.get(eventKind).get(dictKey).update({"type": type[:-7]})
        except Exception as e:
            pass

    @abstractmethod
    def writeToLogFile(self, tag, eventKind, eventDict, timeStamp, toShellOrFile = 3):
        """
        The original standard text file method was 4 tab-separated columns, mouse tag, or 0
        if no single tag was applicaple, unix time stamp, ISO formatted time, and event. Event
        could be anything. Now, every event has a kind, and every kind of event defines a
        dictionary. Main program calls writeToLogFile, as well as the Stimulator object
        For text based methods, event should be a dictionary for more complicated stimulator
        results, so an event can be more easily parsed during data analysis.
        """
        eventTracking  = self.trackingDict.get(eventKind, None)
        if eventKind is "ConsumedReward":
            #Special case :/
            self.trackingDict["Reward"]["consumed"]["values"][tag].pop()
            self.trackingDict["Reward"]["consumed"]["values"][tag].append(True)
        if eventTracking is not None:
            for key in eventDict.keys():
                keyTracking = eventTracking.get(key, None)
                if keyTracking is not None:
                    if keyTracking["type"] is "buffer":
                        if tag not in keyTracking["values"].keys():
                            keyTracking["values"][tag] = deque(maxlen = keyTracking["size"])
                        keyTracking["values"][tag].append(eventDict[key])
                    elif keyTracking["type"] is "totals":
                        if tag not in keyTracking["values"].keys():
                            keyTracking["values"][tag] = 0
                        keyTracking["values"][tag] += eventDict[key]


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
    def getMice(self):
        """
        returns a list of mice that are in the dictionary/database
        """
        pass

    @abstractmethod
    def configGenerator (self):
        """
        generates configuration data for each subject as (IDtag, dictionary) tuples from some kind of permanent storage
        such as a JSON file, or a database. Will be called when program is started, or restarted and settings
        need to be reloaded.
        """
        pass

    @abstractmethod
    def getConfigData (self, tag):
        """
        returns a dictionary of data that was saved for this reference tag, in some permanent storage such as a JSON file
        Will be called when program is started, or restarted and settings need to be reloaded
        """
        pass

    @abstractmethod
    def saveNewMouse(self, tag, note, dictionary):
        """
        store a new mouse entry in a referenced file
        """
        pass

    @abstractmethod
    def retireMouse(self, tag,reason):
        """
        store information about a mouse retirement in a referenced file
        """
        pass

    @abstractmethod
    def storeConfig (self, tag, dictionary, source = ""):
        """
        Stores configuration data, given as an IDtag, and dictionary for that tag, in some more permanent storage
        as a JSON text file, or a database or hd5 file, so it can be later retrieved by IDtag
        """
        pass
