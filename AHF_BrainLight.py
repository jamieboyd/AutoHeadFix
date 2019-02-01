#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from time import sleep
from AHF_Base import AHF_Base

class AHF_BrainLight (AHF_Base, metaclass = ABCMeta):

    defaultDelay = 3.0
           
    @staticmethod
    @abstractmethod
    def config_user_get (starterDict = {}):
        ledDelay = starterDict.get ('ledDelay', AHF_BrainLight.defaultDelay)
        response = input ('Delay in seconds before turning on\after turning off lights (currently %.2f): ' % ledDelay)
        if response != '':
            ledDelay = float (response)
        starterDict.update ({'ledDelay' :  ledDelay})
        return starterDict

        
    @abstractmethod
    def onForStim (self):
        """
        Runs when headFixing starts, illuminating the brain or whatever needs illuminating
        """
        pass

    @abstractmethod
    def offForStim (self):
        """
        Runs when headFixing ends, turning off whatever was turned on
        """
        pass

    def hardwareTest (self):
        """
        generic hardware tester for brain illumination, turns on, waits 2 seconds, turns off
        """
        saveDelay = self.ledDelay
        self.ledDelay =0
        self.onForStim()
        print ('Turning brain illumination ON for two seconds....')
        sleep (2)
        print ('Turning brain illumination OFF.')
        self.offForStim ()
        self.ledDelay = saveDelay
        result = input ('Do you wish to edit brain light settings?')
        if result [0] == 'y' or result [0] == 'Y':
            self.setdown ()
            self.settingsDict.update(self.config_user_get (self.settingsDict))
            self.setup ()
