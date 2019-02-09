#! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_DataLogger (AHF_Base, metaclass = ABCMeta):

    @abstractmethod
    def makeLogFile (self):
        pass

    @abstractmethod
    def writeToLogFile(self, tag, event):
        pass

    @abstractmethod
    def newDay (self, mice):
        pass
