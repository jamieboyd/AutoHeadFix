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
class AHF_Stimulator (object, metaclass = ABCMeta):
    
    """
    Stimulator does all stimulation and reward during a head fix task
    
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.
 
    """

    ##################################################################################
    # Static methods for base class for getting class names and importing classes
    @staticmethod
    def get_class(fileName):
        """
        Imports a module from a fileName (stripped of the .py) and returns the class

        Assumes the class is named the same as the module. 
        """
        module = __import__(fileName)
        return getattr(module, fileName)


    @staticmethod
    def get_Stimulator_from_user ():
        """
        Static method that trawls through current folder looking for Stimulatorer class python files
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_Stimulator_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        """
        iFile=0
        files = ''
        #print (os.listdir(os.curdir))
        for f in os.listdir(os.curdir):
            if f.startswith ('AHF_Stimulator_') and f.endswith ('.py'):
                f= f.rstrip  ('.py')
                #print ('file = ' + str (f))
                try:
                    moduleObj=__import__ (f)
                    #print ('module=' + str (moduleObj))
                    classObj = getattr(moduleObj, moduleObj.__name__)
                    #print ('class obj = ' + str (classObj))
                    isAbstractClass =inspect.isabstract (classObj)
                    if isAbstractClass == False:
                        if iFile > 0:
                            files += ';'
                        files += f
                        iFile += 1
                except Exception as e: # exception will be thrown if imported module imports non-existant modules, for instance
                    print ('Could not load \'' + f + '\':' + str (e))
                    continue     
        if iFile == 0:
            print ('Could not find any AHF_Stimulator files in the current or enclosing directory')
            raise FileNotFoundError
        else:
            if iFile == 1:
                StimulatorFile =  files.split('.')[0]
                print ('Stimulator file found: ' + StimulatorFile)
                StimulatorFile =  files.split('.')[0]
            else:
                inputStr = '\nEnter a number from 0 to ' + str (iFile -1) + ' to Choose a Stimulator class:\n'
                ii=0
                for file in files.split(';'):
                    inputStr += str (ii) + ': ' + file + '\n'
                    ii +=1
                inputStr += ':'
                StimulatorNum = -1
                while StimulatorNum < 0 or StimulatorNum > (iFile -1):
                    StimulatorNum =  int(input (inputStr))
                StimulatorFile =  files.split(';')[StimulatorNum]
                StimulatorFile =  StimulatorFile.split('.')[0]
            return StimulatorFile


    ##################################################################################
    #abstact methods each stimulator class must implement
    @abstractmethod
    def __init__ (self, task):
        pass

    @abstractmethod
    def setup (self):
        pass


    @abstractmethod
    def config_user_get (self):
        pass
    

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
        self.rewarder.giveReward ('task')
        self.mouse.StimulatorRewards += 1
        sleep (10)

    @abstractmethod
    def logFile (self):
        """
            Called after each head fix, prints more detailed text to the log file, perhaps a line for each event

           You may wish to use the same format as writeToLogFile function in __main__.py

           Or you may wish to override with pass and log from the run method
        """
        
        event = 'stim'
        mStr = '{:013}'.format(self.mouse.tag) + '\t'
        outPutStr = mStr + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
        print (outPutStr)
        if self.textfp != None:
            outPutStr = mStr + '{:.2f}'.format (time ()) + '\t' + event
            self.textfp.write(outPutStr + '\n')
            self.textfp.flush()
            

    def nextDay (self, newFP):
        """
            Called when the next day starts. The stimulator is given the new log file pointer. Can do other things as needed
            :param newFP: the file pointer for the new day's log file
        """
        self.textfp = newFP 


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
