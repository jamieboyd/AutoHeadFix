#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_BrainLight (AHF_Base):

    @abstractmethod
    def onForStim (self):
        """
        Runs when headFixing starts, illuminating the brain or whatever needs illuminating
        """
        pass

    @abstractmethod
    def offForStim (self):
        """
        Runs when headFixing ends, turning off whatever was turned on
        """
        pass

    
