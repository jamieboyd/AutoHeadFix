#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base

class AHF_ContactCheck (AHF_Base, metaclass = ABCMeta):

    @abstractmethod
    def checkContact(self):
        return False

    @abstractmethod
    def waitForContact (self, timeoutSecs):
        return False

    @abstractmethod
    def waitForNoContact (self, timeoutSecs):
        return False

    def hardwareTest (self):
        print ('To pass test, start with no contact. Make contact within 10 seconds, then hold contact for less than 10 seconds')
        passed = False
        if self.checkContact():
            print ('Contact is already made. F')
        else:
            print ('Waiting for contact ....')
            if not self.waitForContact (10):
                print ('No contact after waiting for 10 seconds. F')
            else:
                print ('Contact Made!  -  Waiting for contact to be broken....')
                if not self.waitForNoContact (10):
                    print ('Contact maintained for more than 10 seconds. F')
                else:
                    print ('Contact Broken! test passed')
                    passed = True
        if not passed:
            result = input ('Would you like to edit settings for contact check, Y or N?')
            if result[0] == 'Y' or result [0] == 'y':
                self.setdown ()
                self.settingsDict = self.config_user_get (self.settingsDict)
                self.setup()                         

