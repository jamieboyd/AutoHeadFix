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
    def zeroLickCount (self):
        """
        Zeros the array that stores lick counts for each channel
        """
        pass
    
    @abstractmethod
    def getLickCount (self, chanList):
        """
        takes a list of channels and returns a list where each member is the number of licks for that channel in the global array
        call zeroLickCount, wait a while for some licks, then call getLickCount
        """
        pass
    

    def addDataLogger (self, globalTag, dataLogger):
        self.globaltag = globalTag
        if dataLogger is None: 
            self.dataLogger = Simple_Logger (None)
        else:
            self.dataLogger = dataLogger

    
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


class Simple_Logger (object):
    """
    A class to do simple logging of licks, or other events, used if no data logger is passed to lickdetector constructor
    """
    PSEUDO_MUTEX =0
   
    def __init__(self, logFP):
        """
        takes file pointer to a file opened for writing
        If file pointer is none, will just write to shell
        """
        self.logFP = logFP

    
    def writeToLogFile(self, tag, event):
        """
        Writes time of lick to shell, and to a file, if present, in AHF_dataLogger format
        """
        while Simple_Logger.PSEUDO_MUTEX ==1:
            sleep (0.01)
        Simple_Logger.PSEUDO_MUTEX =1
        outPutStr = '{:013}'.format(tag)
        logOutPutStr = outPutStr + '\t' + '{:.2f}'.format (time ())  + '\t' + event +  '\t' + datetime.fromtimestamp (int (time())).isoformat (' ')
        printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
        print (printOutPutStr)
        if self.logFP is not None:
            self.logFP.write(logOutPutStr + '\n')
            self.logFP.flush()
        Simple_Logger.PSEUDO_MUTEX = 0
