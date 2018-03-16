#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os

class AHF_HeadFixer(metaclass = ABCMeta):
    #################################################################################
    # boolean for settability of headFixing levels, default is False. Can be used for incremental learning
    hasLevels = False
    
    ##################################################################################
    # Static methods for base class for getting class names and importing classes
    @staticmethod
    def get_class(fileName):
        """
        Imports a module from a fileName (stripped of the .py) and returns the class

        Assumes the class is named the same as the module
        """
        module = __import__(fileName)
        return getattr(module, fileName)


    @staticmethod
    def get_HeadFixer_from_user ():
        """
        Static method that trawls through current folder looking for HeadFixer class python files
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_HeadFixer_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        """
        iFile=0
        files = ''
        for f in os.listdir('.'):
            if f.startswith ('AHF_HeadFixer_') and f.endswith ('.py'):
                if iFile > 0:
                    files += ';'
                files += f
                iFile += 1
        if iFile == 0:
            print ('Could not find an AHF_HeadFixer_ file in the current or enclosing directory')
            raise FileNotFoundError
        else:
            if iFile == 1:
                print ('Head Fixer file found: ' + stimFile)
                stimFile =  files.split('.')[0]
            else:
                inputStr = '\nEnter a number from 0 to ' + str (iFile -1) + ' to Choose a HeadFixer class:\n'
                ii=0
                for file in files.split(';'):
                    inputStr += str (ii) + ': ' + file + '\n'
                    ii +=1
                inputStr += ':'
                stimFileNum = -1
                while stimFileNum < 0 or stimFileNum > (iFile -1):
                    stimFileNum =  int(input (inputStr))
                stimFile =  files.split(';')[stimFileNum]
                stimFile =  stimFile.split('.')[0]
            return stimFile

    ##################################################################################
    #abstact methods each headfixer class must implement
    #part 1: three main methods of initing, fixing, and releasing
    @abstractmethod
    def __init__(self, cageSet):
        """
        hardware initialization of a headFixer, reading data from a cageSet object
        """
        pass

    @abstractmethod
    def fixMouse(self):
        """
        performs head fixation by energizing a piston, moving a servomotor, etc
        """
        pass
    
    @abstractmethod
    def releaseMouse(self):
        """
        releases mouse from head fixation by relaxing a piston, moving a servomotor, etc
        """
        pass

    ##################################################################################
    #abstact methods each headfixer class must implement
    #part 2: static functions for reading, editing, and saving ConfigDict from/to cageSet

    @staticmethod
    @abstractmethod
    def configDict_read (cageSet,configDict):
        pass

    @staticmethod
    @abstractmethod
    def config_user_get (cageSet,configDict):
        """
        reads data for headFixer configuration from the json configDict, copies it to the cageSet
        """
        pass

    @staticmethod
    @abstractmethod
    def configDict_set (cageSet,configDict):
        """
        gets data from the cageSet object, and updates the json configDict
        """
        pass 

    @staticmethod
    @abstractmethod
    def config_show (cageSet):
        """
        returns a string containing config data for this headFixer currently loaded into the cageSet object
        """
        pass
    

    ##################################################################################
    #abstract methods each headfixer class must implement
    #part 3: hadware tester function
    @abstractmethod
    def test(self, cageSet):
        pass
        """
        Called by hardwaretester, runs a harware test for headFixer, verifying that it works and gives user a chance to save settings
        """
 
    ###################################################################################
    # methods a headFixer will implement if it hasLevels
    # we pass the current level of a particular mouse and level up before head fixing
    # we save the returned new value in the mouse object, for next time

    def level_get_start (self):
        return 0
    
    def level_up (self, baseValue):
        return baseValue + 0

    def level_down (self, baseValue):
        return baseVaue - 0

    def level_set_level (self, level):
        pass
        
    
