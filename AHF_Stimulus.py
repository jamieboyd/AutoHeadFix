#! /usr/bin/python
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_Stimulus(AHF_Base, metaclass = ABCMeta):

    @abstractmethod
    def trialPrep(self, tag):
        """
        Prepares stimulus for trial: e.g. aligns laser, preps vib. motor, etc
        """
        pass

    @abstractmethod
    def stimulate(self):
        pass

    @abstractmethod
    def trialEnd(self):
        """
        Code to be run at end of trial. E.g. moving laser to zero position
        """
        pass
