#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_HeadFixer import AHF_HeadFixer
import RPi.GPIO as GPIO
from time import sleep

class AHF_HeadFixer_Pistons(AHF_HeadFixer):
    """
    Head fixer using solenoid-driven pistons to push head bar against front plate
    a single GPIO output triggers a driver of some kind to energize solenoids
    """
    defaultPin = 12
    @staticmethod
    def about():
        return 'Single GPIO output triggers driver that energize solenoids that push headbar'

    def config_user_get (starterDict = {}):
        """
        Querries user for pin number for piston, returns dictionary 
        """
        starterDict.update (AHF_HeadFixer.config_user_get(starterDict))
        pin = starterDict.get('pistonsPin', AHF_HeadFixer_Pistons.defaultPin)
        response = input ('Enter the GPIO pin connected to the Head Fixing pistons, currently %d:' % pin)
        if response != '':
            pin = int (response)
        starterDict.update ({'pistonsPin': pin})
        return starterDict

    def setup (self):
        hasFixer = True
        super().setup ()
            self.pistonsPin = self.settingsDict.get('pistonsPin')
        try:
            GPIO.setup (self.pistonsPin, GPIO.OUT, initial = GPIO.LOW)
        except Exception as e:
            print (str(e))
            hasFixer = False
        return hasFixer


    def setdown (self):
        GPIO.cleanup (self.pistonsPin)

    def fixMouse(self, resultsDict = {}, settingsDict= {}):
        """
        sets GPIO pin high to trigger pistons
        adds one to headfix results dictionary
        """
        fixed = super().waitForMouse (resultsDict,settingsDict)
        if fixed == self.HAS_CONTACT + self.IS_FIX_TRIAL : # is fixed trial and contact was made
            GPIO.output(self.pistonsPin, GPIO.HIGH)
            sleep (0.5)
            
            if self.task.ContactChecker.checkContact ():
                self.task.DataLogger.writeToLogFile (self.task.tag, 'Fix', {'kind' : 'fixed', 'result' : 'check+'}, time(), 3)
                newFixes = resultsDict.get ('headFixes', 0) + 1
                resultsDict.update ('headFixes' : newFixes)
            else:
                fixed &= ~self.HAS_CONTACT
                GPIO.output(self.pistonsPin, GPIO.LOW)
                self.task.DataLogger.writeToLogFile (self.task.tag, 'Fix', {'kind' : 'fixed', 'result' : 'check-'}, time(), 3)
        elif fixed & self.HAS_CONTACT: #a no-fix trial with contact
            self.task.DataLogger.writeToLogFile (self.task.tag, 'Fix', {'kind' : 'unfixed', 'result' : 'check+'}, time(), 3)
            newUnFixes = resultsDict.get ('unFixes', 0) + 1
            resultsDict.update ('unFixes' : newUnFixes)
        return fixed
            

            
    def releaseMouse(self, resultsDict = {},individualDict= {}):
        """
        sets GPIO pin low to retract pistons
        """
        GPIO.output(self.pistonsPin, GPIO.LOW)
        self.task.lastFixedTag = self.task.tag
        super().releaseMouse (resultsDict, individualDict)
