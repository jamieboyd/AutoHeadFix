#! /usr/bin/python3
#-*-coding: utf-8 -*-
from time import sleep
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_HeadFixer(AHF_Base, metaclass= ABCMeta):
    """
    Base class for all head fix classs. Other head fixers subclass from this, or from one of its subclasses
    boolean for settability of headFixing levels, default is False. Can be used for incremental learning
    """
    hasLevels = False

    
    @abstractmethod
    def fixMouse(self, mouse = None):
        """
        performs head fixation by energizing a piston, moving a servomotor, etc
        """
        pass
    
    @abstractmethod
    def releaseMouse(self, mouse = None):
        """
        releases mouse from head fixation by relaxing a piston, moving a servomotor, etc
        """
        pass


    def hardwareTest (self):
        print (self.__class__.about())
        print ('Head Fixer head-fixing for 2 sec')
        self.fixMouse()
        sleep (2)
        self.releaseMouse ()
        inputStr=input ('Head-Fixer released.\nDo you want to change the Head-Fixer settings?')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.setdown ()
            self.settingsDict = self.__class__.config_user_get (self.settingsDict)
            self.setup()    
