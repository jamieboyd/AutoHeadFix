#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect

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
        if fileName.endswith ('.py'):
            fileName = fileName.rstrip('.py')
        if not fileName.startswith ('AHF_HeadFixer_'):
            fileName = 'AHF_HeadFixer_' + fileName
        try:
            module = __import__(fileName)
            return getattr(module, fileName)
        except ImportError as e:
            print ('Could not import module {}: {}'.format(fileName, str(e)))
            return None
        

    @staticmethod
    def get_HeadFixer_from_user ():
        """
        Static method that trawls through current folder looking for HeadFixer class python files from which user chooses one
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_HeadFixer_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        Returns: name of the file the user chose, stripped of AHF_HeadFixer and .py
        """
        iFile=0
        fileList = []
        startlen = 14
        endlen =3
        for f in os.listdir('.'):
            if f.startswith ('AHF_HeadFixer_') and f.endswith ('.py'):
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
            print ('Could not find an AHF_HeadFixer_ file in the current or enclosing directory')
            raise FileNotFoundError
        else:
            if iFile == 1:
                ClassFile =  fileList[0]
                print ('One  Head Fixer file found: {}'.format (ClassFile))
                return ClassFile
            else:
                inputStr = '\nEnter a number from 1 to {} to choose a Head Fixer file:\n'.format(iFile)

                ii=0
                for file in fileList:
                    inputStr += str (ii + 1) + ': ' + file + '\n'
                    ii +=1
                inputStr += ':'
                classNum = -2
                while classNum < 1 or classNum > iFile:
                    classNum =  int(input (inputStr))
                return fileList[classNum -1]

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
