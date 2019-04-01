#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base
from AHF_Mouse import Mice, Mouse

class AHF_Stimulator (AHF_Base, metaclass = ABCMeta):

    """
    Stimulator does all stimulation and reward during a head fix task
    
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.

    resultsDict 
    """
 

    def config_user_addDictToMouse (self, mouse):
        if hasattr (mouse, 'StimParamDict'):
             mouse.StimParamDict = self.config_user_get(starterDict = mouse.StimParamDict)
        else:
            setattr (mouse, 'StimParamDict', self.config_user_get(starterDict = self.settingsDict))

    


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
        If mouse is None, a list of strings with the keys in the stimulator dictionary is returned.
    
        """
        pass
        
