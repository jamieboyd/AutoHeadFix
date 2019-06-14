#! /usr/bin/python
#-*-coding: utf-8 -*-

from TouchDetectorMPR121 import TouchDetector
from AHF_LickDetector import AHF_LickDetector
import AHF_Task
from time import time

class AHF_LickDetector_MPR (AHF_LickDetector):
    """
    Lick detector for Auto Head Fix based on MPR121 capacitive touch sensor
    """
    defaultIRQ = 26 # GPIO pin for IRQ signal form lick detector, used for triggering callback
    defaultAddress = 0x5a # i2c addresss is 0x5a (90) with address pin tied to ground address will be 0x5b (91) with address pin tied to 3v3
    defaultTouchThresh = 8 # 8 bit value for what constitutes a touch, recommended by dirkjan
    defaultUntouchThresh = 4 # # 8 bit value for what constitutes an un-touch, recommended by dirkjan
    defaultTouchChannels = (0,1,2,3) # number of channels on the mpr121 is 12, but last channel is sum of all channels

    @staticmethod
    def logTouchCallback(touchedChannel):
        """
        custom callback using global task reference from AHF_Task
        """
        AHF_Task.gTask.DataLogger.writeToLogFile(AHF_Task.gTask.tag, 'lick', {'chan' : touchedChannel}, time())
        #newVal = AHF_Task.gTask.Subjects.get(AHF_Task.gTask.tag).get('resultsDict').get('LickDetector', {}).get('licks', 0) + 1
        #AHF_Task.gTask.Subjects.get(AHF_Task.gTask.tag).get('resultsDict').get('LickDetector').update ({'licks' : newVal})


    @staticmethod
    def about ():
        return 'Lick detector using the mpr121 capacitive touch sensor breakout from sparkfun over i2c bus'


    @staticmethod
    def config_user_get (starterDict = {}):
        pin = starterDict.get ('IRQpin', AHF_LickDetector_MPR.defaultIRQ)
        response = input ('Enter the GPIO pin connected to IRQ pin on the MPR121 breakout (currently %d:) ' % pin)
        if response != '':
            pin = int (response)
        mprAddress = starterDict.get ('mprAddress', AHF_LickDetector_MPR.defaultAddress)
        response = input("Enter MPR121 I2C Address, in Hexadecimal, currently 0x%x: " % mprAddress)
        if response != '':
            mprAddress = int (response, 16)
        touchThresh = starterDict.get ('touchThresh', AHF_LickDetector_MPR.defaultTouchThresh)
        response = input ('Enter 8-bit (0-255) touch threshold value, curently %d: ' % touchThresh)
        if response != '':
            touchthresh = int (response)
        unTouchThresh = starterDict.get ('unTouchThresh', AHF_LickDetector_MPR.defaultUntouchThresh)
        response = input ('Enter 8-bit (0-255) un-touch threshold value, curently %d: ' % unTouchThresh)
        if response != '':
            unTouchthresh = int (response)
        touchChans = starterDict.get ('touchChans', AHF_LickDetector_MPR.defaultTouchChannels)
        response = input ('Enter comma-separarted list of channels (0 -11) to monitor, currently {:s}: '.format (str(touchChans)))
        if response != '':
            tempList = []
            for chan in response.split (','):
                tempList.append (chan)
            touchChans = tuple(tempList)
        starterDict.update ({'mprAddress' : mprAddress, 'IRQpin' : pin, 'touchThresh' : touchThresh})
        starterDict.update ({'unTouchThresh' : unTouchThresh, 'touchChans' : touchChans})
        return starterDict


    def setup (self):
        # read dictionary
        self.IRQpin = self.settingsDict.get ('IRQpin')
        self.I2Caddress = self.settingsDict.get ('mprAddress')
        self.touchThresh = self.settingsDict.get ('touchThresh')
        self.unTouchThresh = self.settingsDict.get ('unTouchThresh')
        self.touchChans = self.settingsDict.get ('touchChans')
        self.isLogging = False
        # init touch detector
        self.touchDetector = TouchDetector(self.I2Caddress, self.touchThresh, self.unTouchThresh, self.touchChans, self.IRQpin)
        self.touchDetector.addCustomCallback (self.logTouchCallback)

    def setdown (self):
        del self.touchDetector


    def newResultsDict (self, starterDict = {}):
        """
        Returns a dictionary with fields, initialized to 0,
        """
        starterDict.update ({'licks' : starterDict.get ('licks', 0)})
        return starterDict


    def clearResultsDict(self, resultsDict):
        """
        Clears values in the results dictionary, for daily totals of licks on all channels. Could be extended to per channel data
        """
        resultsDict.update ({'licks' : 0})


    def getTouches (self):
        """
        gets touches from mpr121
        """
        return self.touchDetector.touched ()


    def startLickCount (self):
        """
        Zeros the selected list of channels in the global array of licks per channel that the callback function updates.
        Use it to count licks, by zeroing selected channels, then checking the values in the array
        """
        self.touchDetector.startCount()

    def resumeLickCount (self):
        """
        Continue the lick counting without zeroing the channels
        """
        self.touchDetector.resumeCount()

    def getLickCount (self):
        """
        Get the number of licks for each channel in the global array without stopping the count.
        """
        return self.touchDetector.getCount()


    def stopLickCount (self, chanList):
        """
        takes a list of channels and returns a list where each member is the number of licks for that channel in the global array
        call zeroLickCount, wait a while for some licks, then call getLickCount
        """
        return self.touchDetector.stopCount()


    def startLickTiming (self):
        self.touchDetector.startTimeLog ()


    def stopLickTiming(self):
        return self.touchDetector.stopTimeLog ()


    def startLogging (self):
        """
        tells the AHF_LickDetectorCallback to log touches in shell and file (if present)
        """
        self.touchDetector.startCustomCallback()
        self.isLogging = True

    def stopLogging (self):
        """
        tells the AHF_LickDetectorCallback to stop logging touches in shell and file (if present)
        but the callback is still running
        """
        self.isLogging = False
        self.touchDetector.stopCustomCallback()


    def waitForLick (self, timeOut_secs, startFromZero=False):
        """
        Waits for a lick on any channel. Returns channel that was touched, or 0 if timeout expires with no touch,
        or -1 if startFromZero was True and the detector was touched for entire time
         """
        return self.touchDetector.waitForTouch(timeOut_secs, startFromZero)


    def resetDetector (self):
        """
        Calls MPR121 reset function. Should rarely need to do this? This could be of use in resetting baseline untouched values.
        """
        self.touchDetector._reset ()



    def hardwareTest (self):
        from math import log
        """
        tests the lick detector, designed to be called by the hardware tester,can modify IRQ pin in hardware settings
        """
        wasLogging = False
        if self.isLogging:
            wasLogging = True
            self.stopLogging ()
        lickError = 0
        self.getTouches()
        print ('\nTo pass the test, start with lick spout untouched and touch spout within 10 seconds....')
        lick = self.waitForLick (10, True)
        if lick >= 1:
            print ('PASS:Touch registerd on channel %d' % int (log (lick, 2))) # will round to highest number channel reporting touched
        else:
            if lick == -1:
                rStr= 'FAIL: Touch was registered the whole 10 seconds: '
            else:
                rStr= 'FAIL:No Touches were detected in 10 seconds: '
            inputStr=input (rStr + '\nDo you want to change the lick detetctor settings? :')
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                self.setdown()
                self.settingsDict = self.config_user_get (self.settingsDict)
                self.setup()
            inputStr=input (rStr + '\nDo you want to re-calculate base-line values with a re-set? :')
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                self.resetDetector()
                self.touchDetector.set_thresholds (self.touchThresh, self.unTouchThresh)
        if wasLogging :
            self.startLogging ()
