#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base
from AHF_Mouse import Mice, Mouse

class AHF_Stimulator (AHF_Base, metaclass = ABCMeta):

    """
    Stimulator does all stimulation and reward during a head fix task
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.
    Only needs one special mehtod, the run method
    
    """
 


    @abstractmethod
    def run (self, resultsDict = {}, settingsDict = {}):
        """
        Called at start of each head fix. Does whatever needs tom be done
        """
        pass

        
