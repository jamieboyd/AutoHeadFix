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
        :param fileName: name of a AHF_HeadFixer_ file
        :returns: a reference to the loaded AHF_HeadFixer class
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


    @staticmethod
    @abstractmethod
    def config_user_get (configDict = {}}):
        """
        query user to get configuration settings and update the dictionary
        """
        return configDict

    def __init__(self, cageSet):
        """
        make a local reference to headFixerDict from cageSet object
        """
        self.configDict = cageSet.headFixerDict
        self.setup()
        


    @abstractmethod
    def setup (self):
        """
        make local references from config dict and set up any hardware
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


    def test(self, cageSet):
        """
        Called by hardwaretester, runs a test for a generic headFixer, verifying that it works and gives user a chance to save settings
        """
        inputStr = 'Yes'
        while inputStr[0] == 'y' or inputStr[0] == "Y":
            print ('{:s} head-fixing for 2 seconds'.format (self.__class__.__name__))
            self.fixMouse()
            sleep (2)
            print ('{:s} released'.format (self.__class__.__name__))
            self.releaseMouse()
            inputStr= input('Do you want to edit head fixer settings (yes or no)?')
            if inputStr[0] == 'y' or inputStr[0] == "Y":
               CAD.Edit_dict (cageSet.headFixerDict, self.__class__.__name__)


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
    from AHF_CageSet import AHF_CageSet
    from AHF_HeadFixer import AHF_HeadFixer
    cageSettings = AHF_CageSet ()
    cageSettings.edit()
    headFixer=AHF_HeadFixer.get_class (cageSettings.headFixer) (cageSettings)
    headFixer.test(cageSettings)
    cageSettings.save()
