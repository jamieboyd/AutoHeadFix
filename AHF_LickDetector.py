#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base

class AHF_LickDetector (AHF_Base, metaclass = ABCMeta):
    """
    Base class for lick detetctor. Some kind of touch sensor on water port, capacitive or electrical.
    Should only report touches of the lick port, not un-touches. May have multiple channels. Must be
    able to count licks in an independent thread or via a threaded callback
    """

    @abstractmethod
    def getTouches (self):
        """
        returns number (bit-wise per channel lick detetctor has multiple channels) of which channels are currently touched
        """
        return 0


    @abstractmethod
    def startLickCount (self):
        """
        Zeros the array that stores lick counts for each channel, and makes sure callback is filling the array for requested channels
        """
        pass

    @abstractmethod
    def resumeLickCount (self):
        pass

    @abstractmethod
    def getLickCount (self):
        pass

    @abstractmethod
    def stopLickCount (self):
        """
        takes a tuple of channels and returns a list where each member is the number of licks for that channel in the global array
        call zeroLickCount, wait a while for some licks, then call getLickCount
        """
        pass

    @abstractmethod
    def startLickTiming (self):
        """
        Zeros the array that stores lick counts for each channel, and makes sure callback is filling the array for requested channels
        """
        pass

    @abstractmethod
    def stopLickTiming (self):
        """
        takes a tuple of channels and returns a list where each member is the number of licks for that channel in the global array
        call zeroLickCount, wait a while for some licks, then call getLickCount
        """
        pass

    @abstractmethod
    def startLogging (self):
        """
        Starts the datalogger logging licks to the shell, and to a file if one was provided
        """
        pass


    @abstractmethod
    def stopLogging (self):
        """
        Stops the datalogger logging licks to the shell and file
        """
        pass


    @abstractmethod
    def waitForLick (self, timeOut_secs, startFromZero=False):
        """
        Waits for a lick on any channel. Returns channel that was touched, or 0 if timeout expires with no touch,
        or -1 if startFromZero was True and the detector was touched for entire time
        """
        pass
