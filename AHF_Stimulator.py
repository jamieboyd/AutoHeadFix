#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod
import inspect
import os
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse
import time
import json

from time import time, sleep
from datetime import datetime

class AHF_Stimulator (metaclass = ABCMeta):

    """
    Abstract base class for Stimulator methods, as several exist and we may wish to choose between them at run time

    Stimulator does all stimulation and reward during a head fix task
    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.
    """

    @staticmethod
    def get_class(fileName):
        
        """
        static method that imports a module from a fileName (stripped of the .py) and returns the class, or None if module could not be loaded

        Assumes the class is named the same as the module.
        """
        if fileName.endswith ('.py'):
            fileName = fileName.rstrip('.py')
        if not fileName.startswith ('AHF_Stimulator_'):
            fileName = 'AHF_Stimulator_' + fileName
        try:
            module = __import__(fileName)
            return getattr(module, fileName)
        except ImportError as e:
            print ('Could not import module {}: {}'.format(fileName, str(e)))
            return None
        

    @staticmethod
    def get_Stimulator_from_user ():
        """
        Static method that trawls through current folder looking for Stimulator class python files from which user chooses one
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_Stimulator_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        Returns: name of the file the user chose, stripped of AHF_Settings and .py
        """
        iFile=0
        fileList = []
        startlen = 15
        endlen =3
        for f in os.listdir('.'):
            if f.startswith ('AHF_Stimulator_') and f.endswith ('.py'):
                fname = f[startlen :-endlen]
                try:
                    moduleObj=__import__ (f.rstrip('.py'))
                    #print ('module=' + str (moduleObj))
                    classObj = getattr(moduleObj, moduleObj.__name__)
                    #print (classObj)
                    isAbstractClass = inspect.isabstract (classObj)
                    if isAbstractClass == False:
                        fileList.append (fname)
                        iFile += 1
                except (ImportError, NameError) as e:
                    print ('Could not import module {}: {}'.format(f, str(e)))
                    continue
        if iFile == 0:
            print ('Could not find an AHF_Stimulator_ file in the current or enclosing directory')
            raise FileNotFoundError
        else:
            if iFile == 1:
                ClassFile =  fileList[0]
                print ('One  Stimulator file found: {}'.format (ClassFile))
                return ClassFile
            else:
                inputStr = '\nEnter a number from 1 to {} to choose a Stimulator file:\n'.format(iFile)

                ii=0
                for file in fileList:
                    inputStr += str (ii + 1) + ': ' + file + '\n'
                    ii +=1
                inputStr += ':'
                classNum = -2
                while classNum < 1 or classNum > iFile:
                    classNum =  int(input (inputStr))
                return fileList[classNum -1]

    @staticmethod
    @abstractmethod
    def dict_from_user (stimDict = {}):
        """
        static method that querries user to make or edit a dictionary that holds settings for a stimulator
        subclassses must provide this
        """
        return stimDict
  
    
    def __init__ (self, cageSettings, expSettings, rewarder, lickDetector):
        """
        The Stimulator class is inited with references to cageSettings, experiment settings (includes stimDict)
        and references to the rewarder and lickDetector objects. references are copied to instance variables
        and the setup function is run. Subclasses will probably not need to overwrite this function, but will
        need to provide their own setup function
        """
        self.cageSettings = cageSettings
        self.expSettings = expSettings
        self.rewarder = rewarder
        self.lickDetector = lickDetector
        if not hasattr(expSettings, 'stimDict'):
            setattr(expSettings, 'stimDict', self.dict_from_user ({}))
        self.configDict = expSettings.stimDict
        self.mouse = None
        self.setup()
        

    @abstractmethod
    def setup (self):
        """
        abstract method ubclasses must provide to init any hardware and other resources
        """
        pass
    

    @abstractmethod
    def configStim (self, mouse):
        """
        Called before running each head fix trial, stimulator decides what to do and configures itself

        You may wish to different things for different mice, and to store data about stim presentations in the mouse object
        returns: a short string representing stim configuration, used to generate movie file name
        :param mouse: the object representing the mouse that is currently head-fixed
        """
        return 'stim'


    @abstractmethod
    def run (self):
        """
        Called at start of each head fix. 
        """
        pass
    

    
    def logFile (self):
        """
        Called after each head fix, prints more detailed text to the log file, perhaps a line for each event

        You may wish to use the same format as writeToLogFile function in __main__.py

        Or you may wish to log from the run method
        """
        pass
    

    def nextDay (self, newFP, mice):
        """
            Called when the next day starts. The stimulator is given the new log file pointer. Can do other things as needed
            :param newFP: the file pointer for the new day's log file
        """
        self.textfp = newFP


    def quitting (self):
        """
            Called before AutoHeadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        pass

    def tester (self,expSettings):
        """
            Tester function called from the hardwareTester. Includes Stimulator
            specific hardware tester.
        """
        pass

    def inspect_mice (self,mice,cageSettings,expSettings):
        """
            Helper function to show stimulator specific mouse data.
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
