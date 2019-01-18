#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod
import os
import inspect

"""
from AHF_LickDetector import LickDetector
from AHF_Mouse import Mouse
import time
import json
import os
from time import time, s leep
from datetime import datetime
"""
class AHF_Stimulator (metaclass = ABCMeta):

    
    """
    Stimulator does all stimulation and reward during a head fix task
    
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.
 
    """
    
    @staticmethod
    def about ():
        return 'about message for this stimulator class goes here'
  

    ##################################################################################
    #abstact methods each stimulator class must implement
    @abstractmethod
    def __init__ (self, taskP):
        pass

    @abstractmethod
    def setup (self):
        pass

    @staticmethod
    @abstractmethod
    def config_user_get ():
        return {}
    

    @abstractmethod
    def configStim (self, mouse):
        """
        Called before running each head fix trial, stimulator decides what to do and configures itself

        You may wish to different things for different mice, and to store data about stim presentations in the mouse object
        returns: a short string representing stim configuration, used to generate movie file name
        :param mouse: the object representing the mouse that is currently head-fixed
        """
        if 'stimCount' in mouse.stimResultsDict:
            mouse.stimResultsDict.update ({'stimCount' : mouse.stimResultsDict.get('stimCount') + 1})
        else:
            mouse.stimResultsDict.update({'stimCount' : 1})

        self.mouse = mouse
        return 'stim'
         
    @abstractmethod
    def run (self):
        """
        Called at start of each head fix. Gives a reward, increments mouse's reward count, then waits 10 seconds
        """
        pass

    @abstractmethod
    def logFile (self):
        """
            Called after each head fix, prints more detailed text to the log file, perhaps a line for each event

           You may wish to use the same format as writeToLogFile function in __main__.py

           Or you may wish to override with pass and log from the run method
        """
        pass
            

    def nextDay (self, newFP):
        """
            Called when the next day starts. The stimulator is given the new log file pointer. Can do other things as needed
            :param newFP: the file pointer for the new day's log file
        """
        pass


    def quitting (self):
        """
            Called before AutoHEadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        pass



if __name__ == '__main__':
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    rewarder = AHF_Rewarder (30e-03, 24)
    rewarder.addToDict ('task', 50e-03)
    thisMouse = Mouse (2525, 0,0,0,0, '')
    stimFile = AHF_Stimulator.get_stimulator_from_user ()
    stimDict = AHF_Stimulator.get_class (stimFile).dict_from_user({})
    stimulator = AHF_Stimulator.get_class (stimFile)(stimDict, rewarder, None)
    print (stimulator.configStim (thisMouse))
    stimulator.run ()
    stimulator.logFile()
    stimulator.config_from_user()
    print (stimulator.configStim (thisMouse))
    stimulator.run ()
    stimulator.logFile()
    thisMouse.show()
    GPIO.cleanup ()
