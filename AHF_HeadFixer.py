#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import AHF_ClassAndDictUtils as CAD

class AHF_HeadFixer(metaclass = ABCMeta):
    """
    Abstract base class for Head Fix methods, as several exist and we may wish to choose between them at run time
    """
    hasLevels = False # boolean for settability of headFixing levels, default is False. Can be used for incremental learning
    
    @staticmethod
    def get_class(fileName):
        
        """
        static method that imports a module from a fileName (stripped of the .py) and returns the class, or None if module could not be loaded

        Assumes the class is named the same as the module.
        """
        return CAD.Class_from_file('HeadFixer', fileName.rstrip('.py').lstrip('AHF_HeadFixer_'))
         

    @staticmethod
    def get_HeadFixer_from_user ():
        """
        Static method that trawls through current folder looking for HeadFixer class python files from which user chooses one
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_HeadFixer_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        Returns: name of the file the user chose, stripped of AHF_HeadFixer and .py
        """
        return CAD.Subclass_from_user(CAD.Class_from_file('HeadFixer', ''))
 
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
        
    
if __name__ == "__main__":
    from time import sleep
    from AHF_CageSet import AHF_CageSet
    from AHF_HeadFixer import AHF_HeadFixer
    cageSettings = AHF_CageSet ()
    cageSettings.edit()
    headFixer=AHF_HeadFixer.get_class (cageSettings.headFixer) (cageSettings)
    headFixer.test(cageSettings)
    cageSettings.save()
