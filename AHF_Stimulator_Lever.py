 #! /usr/bin/python
#-*-coding: utf-8 -*


from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse
from Pywith import Pulse, Train
import time
import json

class AHF_Stimulator_Lever (AHF_Stimulator):
    """
        AHF_Stimulator_Lever runs a lever task by calling c++ code that
        records lever position and puts torque on the lever
    """

    def __init__ (self, configDict, rewarder, textfp):
        super().__init__(configDict, rewarder, textfp)
        self.setup()


     @staticmethod
    def dict_from_user (stimDict):
        if not 'dataSaveFolder' in stimDict:
            stimDict.update ({'dataSaveFolder' : '/home/pi/Documents/'})
                
        if not 'decoderReversed' in stimDict:
            stimDict.update ({'decoderReversed' : False})
        if not 'motorPresent' in stimDict:
            stimDict.update ({'motorPresent' : True})
        if not 'motorHasDirection' in stimDict:
            stimDict.update ({'motorHasDirection' : True})
        if not 'motorDirectionPin' in stimDict:
            stimDict.update ({'motorDirectionPin' : 18})
        if not 'startCuePin' in stimDict:
            stimDict.update ({'startCuePin' : 17})
        return super(AHF_Stimulator_Lever, AHF_Stimulator_Lever).dict_from_user (stimDict)
