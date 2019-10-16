#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_ContactCheck_Elec import AHF_ContactCheck_Elec

class AHF_ContactCheck_BeamBreak(AHF_ContactCheck_Elec):
    defaultPin = 12
    defaultLEDPin = 24

    @staticmethod
    def about():
        return 'Beam-Break contact checker for Adafruit IR Beam Break Sensors'

    @staticmethod
    def config_user_get(starterDict = {}):
        contactPin = starterDict.get('contactPin', AHF_ContactCheck_BeamBreak.defaultPin)
        response = input('Enter the GPIO pin connected to the IR beam-breaker, currently %d:' % contactPin)
        if response != '':
            contactPin = int(response)
        ledPin = starterDict.get('contactPin', AHF_ContactCheck_BeamBreak.defaultLEDPin)
        response = input('Enter the GPIO pin connected to the IR beam-breaker, currently %d:' % ledPin)
        if response != '':
            ledPin = int(response)
        starterDict.update({'contactPin': contactPin, 'contactPolarity' : 'FALLING', 'contactPUD' : 'PUD_UP', 'ledPin': ledPin})
        return starterDict

    def setup(self):
        super().setup()
        self.ledPin = self.settingsDict.get('ledPin')
        GPIO.setup(self.ledPin, GPIO.OUT)
        GPIO.output(self.ledPin, GPIO.LOW)


    def turnOff(self):
        GPIO.output(self.ledPin, GPIO.HIGH)

    def turnOn(self):
        GPIO.output(self.ledPin, GPIO.LOW)
