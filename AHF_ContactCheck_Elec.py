#! /usr/bin/python3
#-*-coding: utf-8 -*-
import RPi.GPIO as GPIO
from time import time, sleep
from AHF_ContactCheck import AHF_ContactCheck
import AHF_Task

gContactChecker = None

class AHF_ContactCheck_Elec (AHF_ContactCheck):

    defaultPin = 12
    defaultPolarity = 'FALLING'
    defaultPUD = 'PUD_UP'
    debounceTime = 0.1 #seconds

    @staticmethod
    def contactCheckCallback (channel):
        """
        Contacts are immediate, but un-contacts are delayed
        """
        global gContactChecker
        contact = gContactChecker.checkContact ()
        duration = time() - AHF_Task.gTask.contactTime
        if contact:
            print("Contact!")
            AHF_Task.gTask.contact = True
            AHF_Task.gTask.contactTime = time()
        if contact == False and (duration > AHF_ContactCheck_Elec.debounceTime):
            AHF_Task.gTask.contact = False
        elif contact == False:
            sleep(AHF_ContactCheck_Elec.debounceTime)
            contact = gContactChecker.checkContact ()
            if contact == False:
                AHF_Task.gTask.contact = False

    @staticmethod
    def about ():
        return 'Simple electrical contact check with option for pull-up or pull-down resistor.'

    @staticmethod
    def config_user_get (starterDict = {}):
        # GPIO pin used for contact check
        contactPin = starterDict.get ('contactPin', AHF_ContactCheck_Elec.defaultPin)
        response = input ('Enter the GPIO pin connected to the electrical contact, currently %d:' % contactPin)
        if response != '':
            contactPin = int (response)
        # polarity - rising or falling when making contact
        contactPolarity = starterDict.get ('contactPolarity', AHF_ContactCheck_Elec.defaultPolarity)
        response = input ('Enter the polarity for making contact, R for Rising or F for Falling, currently %s:' % contactPolarity)
        if response != '':
            if response [0]== 'R' or response [0]== 'r':
                response = 'RISING'
            else:
                contactPolarity = 'FALLING'
        # Falling contact may have a pull-up resistor, rising contact may have a pull-down resistor
        contactPUD = starterDict.get ('contactPUD', AHF_ContactCheck_Elec.defaultPUD)
        onoff = 'enabled'
        if contactPUD == 'PUD_OFF':
            onoff = 'not enabled'
        updown = 'pull-up'
        if contactPolarity == 'RISING':
            updown = 'pull-down'

        response = input ('Enable %s resistor on the GPIO pin? enter Yes to enable, or No if an external pull-up is installed, currently %s:' % (updown, onoff))
        if response != '':
            if response [0]== 'N' or response [0]== 'n':
                contactPUD = 'PUD_OFF'
            elif contactPolarity == 'RISING':
                contactPUD='PUD_DOWN'
            else:
                contactPUD = 'PUD_UP'
        starterDict.update ({'contactPin': contactPin, 'contactPolarity' : contactPolarity, 'contactPUD' : contactPUD})
        return starterDict


    def setup (self):
        self.contactPin = self.settingsDict.get ('contactPin')
        self.contactPolarity = getattr (GPIO, self.settingsDict.get ('contactPolarity'))
        self.contactState = GPIO.HIGH
        self.unContactPolarity =GPIO.RISING
        if self.contactPolarity == GPIO.FALLING:
            self.contactState = GPIO.LOW
            self.unContactPolarity = GPIO.RISING
        self.contactPUD = getattr (GPIO, self.settingsDict.get ('contactPUD'))
        hasContact = True
        try:
            GPIO.setmode (GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup (self.contactPin, GPIO.IN, pull_up_down =self.contactPUD)
            global gContactChecker
            gContactChecker = self
        except Exception as e:
            print (str(e))
            hasContact = False
        return hasContact


    def setdown (self):
        GPIO.cleanup(self.contactPin)

    def checkContact(self):
        if (GPIO.input (self.contactPin)== self.contactState):
            return True
        else:
            return False

    def waitForContact(self, timeOutSecs):
        if GPIO.wait_for_edge (self.contactPin, self.contactPolarity, timeout= int (timeOutSecs * 1e03)) is None:
            return False
        else:
            return True


    def waitForNoContact (self, timeOutSecs):
        if GPIO.wait_for_edge (self.contactPin, self.unContactPolarity, timeout= int (timeOutSecs * 1e03)) is None:
            return False
        else:
            return True

    def startLogging (self):
        GPIO.add_event_detect (self.contactPin, GPIO.BOTH)
        GPIO.add_event_callback (self.contactPin, self.contactCheckCallback)

    def stopLogging (self):
        GPIO.remove_event_detect (self.contactPin)
