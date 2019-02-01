#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_ContactCheck_Elec import AHF_ContactCheck_Elec

class AHF_ContactCheck_BeamBreak (AHF_ContactCheck_Elec):
    defaultPin = 21
    
    @staticmethod
    def about ():
        return 'Beam-Break contact checker for Adafruit IR Beam Break Sensors'
    
    @staticmethod
    def config_user_get (starterDict = {}):
        contactPin = starterDict.get ('contactPin', AHF_ContactCheck_BeamBreak.defaultPin)
        response = input ('Enter the GPIO pin connected to the IR beam-breaker, currently %d:' % contactPin)
        if response != '':
            contactPin = int (response)
        starterDict.update({'contactPin': contactPin, 'contactPolarity' : 'FALLING', 'contactPUD' : 'PUD_UP'})
        return starterDict


    
