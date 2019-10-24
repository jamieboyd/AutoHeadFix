#! /usr/bin/python
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_Stimulus(AHF_Base, metaclass = ABCMeta):
    """
    Generic "Stimulus" for use in Stimulators. Interacts with the mouse in
    some defined method based on the type of stimulus. Examples include a
    vibration motor, laser pulse in a specific brain region, or nothing.
    """

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

    @abstractmethod
    def length(self):
        """
        Return length of stimulus (e.g. pulse duration)
        """
        pass

    @abstractmethod
    def period(self):
        """
        Return period of stimulus (1/frequency for motor/laser)
        """
        pass
