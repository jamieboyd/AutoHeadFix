#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect
from AHF_ContactCheck import AHF_ContactCheck
import RPi.GPIO as GPIO

class AHF_ContactCheck_BeamBreak (AHF_ContactCheck):

    @staticmethod
    def config_user_get ():
        contactDict={}
        contactPin = int (input ('Enter the GPIO pin connected to the IR beam-breaker:'))
        contactDict.update ('contactPin': contactPin)
        return contactDict


    def __init__ (self, ContactCheckDict):
        self.contactDict = ContactCheckDict
        self.contactPin = 0
        self.setup()


    def setup (self):
        if self.contactPin != 0:
            GPIO.cleanup (self.contactPin)
        self.contactPin =contactDict.get('contactPin')
        GPIO.setup (self.contactPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)


    def checkContact(self):
        if (GPIO.input (self.contactPin)== GPIO.HIGH):
            return True
        else:
            return False

    def waitForContact(self, timeOutSecs):
        if GPIO.wait_for_edge (self.contactPin, GPIO.FALLING, timeout= timeOutSecs) is None:
            return False
        else:
            return True

        
