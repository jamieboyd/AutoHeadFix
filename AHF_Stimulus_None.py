#! /usr/bin/python
#-*-coding: utf-8 -*-
from AHF_Stimulus import AHF_Stimulus

class AHF_Stimulus_None (AHF_Stimulus):
    
    @staticmethod
    def about():
        return "Does nothing"
        
    def hardwareTest(self):
        pass

    def trialPrep (self):
        """
        Prepares stimulus for trial: e.g. aligns laser, preps vib. motor, etc
        """
        return True

    def stimulate (self):
        pass
    
    @staticmethod
    def config_user_get(starterDict= {}):
        return starterDict
    
    def setup(self):
        pass
    
    def setdown(self):
        pass

    def trialEnd (self):
        """
        Code to be run at end of trial. E.g. moving laser to zero position
        """
        pass

