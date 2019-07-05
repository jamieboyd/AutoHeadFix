#! /usr/bin/python
#-*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod
from inspect import isabstract
from os import listdir
from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse
from collections import OrderedDict

from time import time, sleep
from datetime import datetime

class AHF_Stimulator (metaclass = ABCMeta):

    """
    Abstract base class for Stimulator methods, as several exist and we may wish to choose between them at run time

    Stimulator does and reward during a head fix task
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
        for f in listdir('.'):
            if f.startswith ('AHF_Stimulator_') and f.endswith ('.py'):
                fname = f[startlen :-endlen]
                try:
                    moduleObj=__import__ (f.rstrip('.py'))
                    #print ('module=' + str (moduleObj))
                    classObj = getattr(moduleObj, moduleObj.__name__)
                    #print (classObj)
                    isAbstractClass = isabstract (classObj)
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


    @staticmethod
    def Show_ordered_dict (objectDict, longName):
        """
        Dumps standard dictionary settings into an ordered dictionary, prints settings to screen in a numbered fashion from the ordered dictionary,
        making it easy to select a setting to change. Returns an  ordered dictionary of {number: (key:value),} used by edit_dict function
        """
        print ('\n*************** Current {:s} Settings *******************'.format (longName))
        showDict = OrderedDict()
        itemDict = {}
        nP = 0
        for key in sorted (objectDict) :
            value = objectDict.get (key)
            showDict.update ({nP:{key: value}})
            nP += 1
        for ii in range (0, nP):
            itemDict.update (showDict [ii])
            kvp = itemDict.popitem()
            print ('{:d}) {:s} = {}'.format (ii + 1, kvp [0], kvp [1]))
        print ('**********************************\n')
        return showDict

    @staticmethod
    def Edit_dict (anyDict, longName):
        """
        Edits values in a passed in dict, in a generic way, not having to know ahead of time the name and type of each setting
        Assumption is made that lists/tuples contain only strings, ints, or float types, and that all members of any list/tuple are same type
        """
        while True:
            orderedDict = AHF_Stimulator.Show_ordered_dict (anyDict, longName)
            updatDict = {}
            inputStr = input ('Enter number of setting to edit, or 0 to exit:')
            try:
                inputNum = int (inputStr)
            except ValueError as e:
                print ('enter a NUMBER for setting, please: %s\n' % str(e))
                continue
            if inputNum == 0:
                break
            else:
                itemDict = orderedDict.get (inputNum -1)
                kvp = itemDict.popitem()
                itemKey = kvp [0]
                itemValue = kvp [1]
                if type (itemValue) is str:
                    inputStr = input ('Enter a new text value for %s, currently %s:' % (itemKey, str (itemValue)))
                    updatDict = {itemKey: inputStr}
                elif type (itemValue) is int:
                    inputStr = input ('Enter a new integer value for %s, currently %s:' % (itemKey, str (itemValue)))
                    updatDict = {itemKey: int (inputStr)}
                elif type (itemValue) is float:
                    inputStr = input ('Enter a new floating point value for %s, currently %s:' % (itemKey, str (itemValue)))
                    updatDict = {itemKey: float (inputStr)}
                elif type (itemValue) is tuple or itemValue is list:
                    outputList = []
                    if type (itemValue [0]) is str:
                        inputStr = input ('Enter a new comma separated list of strings for %s, currently %s:' % (itemKey, str (itemValue)))
                        outputList = list (inputStr.split(','))
                    elif type (itemValue [0]) is int:
                        inputStr = input ('Enter a new comma separated list of integer values for %s, currently %s:' % (itemKey, str (itemValue)))
                        for string in inputStr.split(','):
                            try:
                                outputList.append (int (string))
                            except ValueError:
                                continue
                    elif type (itemValue [0]) is float:
                        inputStr = input ('Enter a new comma separated list of floating point values for %s, currently %s:' % (itemKey, str (itemValue)))
                        for string in inputStr.split(','):
                            try:
                                outputList.append (float (string))
                            except ValueError:
                                continue
                    if type (itemValue) is tuple:
                        updatDict = {itemKey: tuple (outputList)}
                    else:
                        updatDict = {itemKey: outputList}
                elif type (itemValue) is bool:
                    inputStr = input ('%s, True for or False?, currently %s:' % (itemKey, str (itemValue)))
                    if inputStr [0] == 'T' or inputStr [0] == 't':
                        updatDict = {itemKey: True}
                    else:
                        updatDict = {itemKey: False}
                elif type (itemValue) is dict:
                    Edit_dict (itemValue, itemKey)
                    anyDict[itemKey].update (itemValue)
                anyDict.update (updatDict)
  
    
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
        abstract method subclasses must provide to init any hardware and other resources
        """
        pass
    

    @abstractmethod
    def configStim (self, mouse):
        """
        Called before running each head fix trial, stimulator decides what to do and configures itself

        You may wish to different things for different mice, and to store data about stim presentations in the mouse object
        :returns: a short string representing stim configuration, used to generate movie file name
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

    def tester (self):
        """
            Tester function called from the hardwareTester. Includes Stimulator
            specific hardware tester.
        """
        pass

    def inspect_mice (self):
        """
            Helper function to show stimulator specific mouse data.
        """
        pass


