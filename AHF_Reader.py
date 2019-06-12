#! /usr/bin/python
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_Reader (AHF_Base, metaclass = ABCMeta):

    @abstractmethod
    def readTag (self):
        pass

    @abstractmethod
    def startLogging (self):
        """
        starts using data logger to start logging entries/exits
        """
        pass

    @abstractmethod
    def stopLogging (self):
        """
        stops  data logger from logging entries/exits
        """
