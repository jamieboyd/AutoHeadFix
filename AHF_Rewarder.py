#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect

class AHF_Rewarder(metaclass = ABCMeta):
    """
    Base class for all rewarder classs. Other rewarders subclass from this, or from one of its subclasses
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
    def get_Rewarder_from_user ():
        """
        Static method that trawls through current folder looking for Rewarder class python files
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_Rewarder_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        """
        iFile=0
        files = ''
        #print (os.listdir(os.curdir))
        for f in os.listdir(os.curdir):
            if f.startswith ('AHF_Rewarder_') and f.endswith ('.py'):
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
                    print (e)
                    continue     
        if iFile == 0:
            print ('Could not find any AHF_Rewarder_ files in the current or enclosing directory')
            raise FileNotFoundError
        else:
            if iFile == 1:
                RewarderFile =  files.split('.')[0]
                print ('Rewarder file found: ' + RewarderFile)
                RewarderFile =  files.split('.')[0]
            else:
                inputStr = '\nEnter a number from 0 to ' + str (iFile -1) + ' to Choose a Rewarder class:\n'
                ii=0
                for file in files.split(';'):
                    inputStr += str (ii) + ': ' + file + '\n'
                    ii +=1
                inputStr += ':'
                rewarderNum = -1
                while rewarderNum < 0 or rewarderNum > (iFile -1):
                    rewarderNum =  int(input (inputStr))
                RewarderFile =  files.split(';')[rewarderNum]
                RewarderFile =  RewarderFile.split('.')[0]
            return RewarderFile

    @staticmethod
    @abstractmethod
    def config_user_get ():
        return {}


    @abstractmethod
    def __init__ (self, rewarderDict):
        pass

    @abstractmethod
    def setup (self):
        pass


    @abstractmethod
    def giveReward(self, rewardName):
        return 0

    @abstractmethod
    def giveRewardCM(self, rewardName):
        return 0


    @abstractmethod
    def countermandReward(self):
        return 0

    @abstractmethod
    def hardwareTest (self):
        pass


    def showSettings (self):
        """
        Prints settings to screen in a numbered fashion from an ordered dictionary, making it easy to select a setting to
        change. Returns the ordered dictionary, used by editSettings function
        """
        print ('*************** Current Rewarder Settings *******************')
        showDict = OrderedDict()
        itemDict = {}
        nP = 0
        for key, value in self.rewarderDict:
        #for key, value in inspect.getmembers(self):
            showDict.update ({nP:{key: value}})
            nP += 1
        for ii in range (0, np):
            itemDict.update (showDict [ii])
            kvp = itemDict.popitem()
            print(str (ii) +') ', kvp [0], ' = ', kvp [1])
        print ('**********************************\n')
        return showDict
    

    def editSettings (self):
        itemDict = {}
        while True:
            showDict = self.showSettings()
            inputNum = int (input ('Enter number of setting to edit, or -1 to exit:'))
            if inputNum == 0:
                break
            else:
                itemDict.update (showDict [inputNum])
                kvp = itemDict.popitem()
                itemKey = kvp [0]
                itemValue = kvp [1]
                if type (itemValue) is str:
                    inputStr = input ('Enter a new text value for %s, currently %s:' % itemKey, str (itemValue))
                    self.rewarderDict.update ({itemKey: inputStr})
                elif type (itemValue) is int:
                    inputStr = input ('Enter a new integer value for %s, currently %s:' % itemKey, str (itemValue))
                    self.rewarderDict.update ({itemKey: int (inputStr)})
                elif type (itemValue) is float:
                    inputStr = input ('Enter a new floating point value for %s, currently %s:' % itemKey, str (itemValue))
                    self.rewarderDict.update ({itemKey: float (inputStr)})
                elif type (itemValue) is tuple:
                    inputStr = input ('Enter a new comma separated list for %s, currently %s:' % itemKey, str (itemValue))
                    self.rewarderDict.update ({itemKey: tuple (inputStr.split(','))})
                elif type (itemVale) is bool:
                    inputStr = input ('%s, True for or False?, currently %s:' % itemKey, str (itemValue))
                    if inputStr [0] == 'T' or inputStr [0] == 't':
                        self.rewarderDict.update ({itemKey: True})
                    else:
                        self.rewarderDict.update ({itemKey: False})
        self.setup()    
