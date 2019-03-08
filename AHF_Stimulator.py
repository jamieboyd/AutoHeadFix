#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod
import os
import inspect

from AHF_Base import AHF_Base

class AHF_Stimulator (AHF_Base, metaclass = ABCMeta):

    """
    Stimulator does all stimulation and reward during a head fix task
    
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.
 
    """

    @abstractmethod
    def run (self, mouse):
        """
        Called at start of each head fix.
        """
        pass

    

    @abstractmethod
    def configMouse (self, mouse):
        """
        adds attributes to a mouse object to store whatever data needs to be stored between stimulator runs
        """
        pass

    @abstractmethod
    def MousePrecis (self, mouse):
        """
        Returns a dictionary of daily results for an individual mouse. Number of trials, % correct, learning level, if applicable
        The items in the Precis dictionary will probably be the same as in the configMouse
    
        """
        pass
