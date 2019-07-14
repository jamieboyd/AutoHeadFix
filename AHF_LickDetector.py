#! /usr/bin/python
#-*-coding: utf-8 -*-

from TouchDetectorMPR121 import TouchDetector
import RFIDTagReader
from time import time
from datetime import datetime
global gLogFP

class AHF_LickDetector (object):
    
    defaultAddress = 0x5a
    defaultTouchThresh = 12
    defaultUnTouchThresh = 8


    @staticmethod
    def lickLoggerCallback (touchedPin):

        now = time ()
        nowISO=datetime.fromtimestamp (int (now)).isoformat (' ')
        logStr = '{:013}\t{:.2f}\tlick:{:d}\t{:s}\n'.format(RFIDTagReader.globalTag, now, touchedPin, nowISO)
        if gLogFP is not None:
            gLogFP.write(logStr)
        printStr = '{:013}\tlick:{:d}\t{:s}'.format(RFIDTagReader.globalTag, touchedPin, nowISO)          
        print (printStr)
 
    
    def __init__ (self, lickChans, lickIRQPin, logFP):
        self.touchDetector = TouchDetector (AHF_LickDetector.defaultAddress, AHF_LickDetector.defaultTouchThresh, AHF_LickDetector.defaultUnTouchThresh, lickChans, lickIRQPin)
        global gLogFP
        gLogFP = logFP
        self.touchDetector.addCustomCallback(AHF_LickDetector.lickLoggerCallback)
        

    def start_logging (self):
        self.touchDetector.startCustomCallback()
    

    def stop_logging (self):
        self.touchDetector.stopCustomCallback()

    def wait_for_lick (self, timeOut_secs, startFromZero=False):
        return self.touchDetector.waitForTouch (timeOut_secs, startFromZero)


    def touched(self):
        return self.touchDetector.touched()

    def reset (self):
        self.touchDetector.reset ()


    def test (self, cageSet):
        from math import log2, floor
        wasLogging = self.touchDetector.callbackMode & TouchDetector.callbackCustomMode
        if wasLogging:
            self.stop_logging ()
        print ('Lick detetctor waiting 5 seconds for a touch....')
        lick = self.wait_for_lick (5, True)
        if lick == 0:
            inputStr= input('No licks detected. Do you want to change IRQ pin, currently {:d} ?'.format (self.touchDetector.IRQpin))
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                cageSet.lickIRQ = int (input('Enter New Lick Detector IRQ pin:'))
                self.touchDetector.changeIRQpin (cageSet.lickIRQ)
        elif lick == -1:
            inputStr= input('lick detector registered a touch for the entire 5 seconds. Do you want to do a soft reset of the lick detector ?')
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                self.touchDetector.reset ()
        else:
            print ('Lick detector registered a touch on pin {:d}'.format(floor(log2(lick))))
        if wasLogging:
            self.start_logging ()

