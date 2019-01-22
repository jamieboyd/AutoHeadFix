#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect

class AHF_ContactCheck (metaclass = ABCMeta):

    @staticmethod
    def about ():
        return 'about message for this contact checker class goes here'


    @staticmethod
    @abstractmethod
    def config_user_get ():
        return {}


    @abstractmethod
    def __init__ (self, ContactCheckDict):
        pass

    @abstractmethod
    def setup (self):
        pass


    @abstractmethod
    def checkContact(self):
        return False

    @abstractmethod
    def waitForContact (self, timeoutSecs):
        pass

    @abstractmethod
    def hardwareTest (self):
        pass




    def showSettings (self):
        """
        Prints settings to screen in a numbered fashion from an ordered dictionary, making it easy to select a setting to
        change. Returns the ordered dictionary, used by editSettings function
        """
        print ('*************** Current ContactCheck Settings *******************')
        showDict = OrderedDict()
        itemDict = {}
        nP = 0
        for key, value in self.ContactCheckDict:
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
                    self.ContactCheckDict.update ({itemKey: inputStr})
                elif type (itemValue) is int:
                    inputStr = input ('Enter a new integer value for %s, currently %s:' % itemKey, str (itemValue))
                    self.ContactCheckDict.update ({itemKey: int (inputStr)})
                elif type (itemValue) is float:
                    inputStr = input ('Enter a new floating point value for %s, currently %s:' % itemKey, str (itemValue))
                    self.ContactCheckDict.update ({itemKey: float (inputStr)})
                elif type (itemValue) is tuple:
                    inputStr = input ('Enter a new comma separated list for %s, currently %s:' % itemKey, str (itemValue))
                    self.ContactCheckDict.update ({itemKey: tuple (inputStr.split(','))})
                elif type (itemVale) is bool:
                    inputStr = input ('%s, True or False?, currently %s:' % itemKey, str (itemValue))
                    if inputStr [0] == 'T' or inputStr [0] == 't':
                        self.ContactCheckDict.update ({itemKey: True})
                    else:
                        self.ContactCheckDict.update ({itemKey: False})
        self.setup()
