#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect
from AHF_ContactCheck import AHF_ContactCheck

class AHF_ContactCheck_Elec (AHF_ContactCheck):
    

            fileErr = True
            tempInput = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
            if tempInput == 0:
                self.contactPolarity = 'FALLING'
            else:
                self.contactPolarity = 'RISING'
            tempInput = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
            if tempInput == 0:
                self.contactPUD = 'PUD_OFF'
            elif tempInput == 1:
                self.contactPUD = 'PUD_DOWN'
            else:
                self.contactPUD='PUD_UP'
            fileErr = True
