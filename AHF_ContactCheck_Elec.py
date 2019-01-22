#! /usr/bin/python3
#-*-coding: utf-8 -*-
import RPi.GPIO as GPIO
from AHF_ContactCheck import AHF_ContactCheck

class AHF_ContactCheck_Elec (AHF_ContactCheck):

    @staticmethod
    def about ():
        return 'Simple electrical contact check with pull-up or pull-down resistor.'


    @staticmethod
    def config_user_get ():
        contactPin = int (input ('Enter the GPIO pin connected to the electrical contact:'))
        tempInput = input ('Enter the contact polarity, R for Rising or F for Falling when contact is made:')
        if tempInput [0]== 'R' or tempInput [0]== 'r':
            contactPolarity = 'RISING'
        else:
            contactPolarity = 'FALLING'

        if contactPolarity == GPIO.RISING:
            inputStr = 'Enable pull-down resistor on the GPIO pin? enter Yes to enable, or No if an external pull-up is installed:'
        else:
            inputStr = 'Enable pull-up resistor on the GPIO pin? enter Yes to enable, or No if an external pull-up is installed:'  
        tempInput = input(inputStr)
        if tempInput [0]== 'N' or tempInput [0]== 'n':
            contactPUD = 'PUD_OFF'
        elif contactPolarity == 'RISING':
            contactPUD='PUD_DOWN'
        else:
            contactPUD = 'PUD_UP'
        contactDict = {'contactPin': contactPin, 'contactPolarity' : contactPolarity, 'contactPUD' : contactPUD}
        return contactDict


    def __init__ (self, ContactCheckDict):
        self.contactDict = ContactCheckDict
        self.contactPin = self.contactDict.get ('contactPin', 21)
        self.contactPolarity = self.contactDict.get ('contactPolarity', 'RISING')
        self.contactPUD = self.contactDict.get ('contactPUD', 'PUD_DOWN')
        self.setup()


    def setup (self):
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.cleanup (self.contactPin)
        GPIO.setup (self.contactPin, GPIO.IN, pull_up_down = getattr (GPIO, self.contactPUD))


    def checkContact(self):
        if (GPIO.input (self.contactPin)== GPIO.HIGH):
            return True
        else:
            return False

    def waitForContact(self, timeOutSecs):
        if GPIO.wait_for_edge (self.contactPin, getattr (GPIO, self.contactPolarity), timeout= timeOutSecs) is None:
            return False
        else:
            return True


    def hardwareTest (self):
        pass


        
