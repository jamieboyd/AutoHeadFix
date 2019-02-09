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
        Called at start of each head fix. Gives a reward, increments mouse's reward count, then waits 10 seconds
        """
        pass

            
    @abstractmethod
    def nextDay (self):
        """
            Called when the next day starts. The stimulator is given the new log file pointer. Can do other things as needed
            :param newFP: the file pointer for the new day's log file
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
