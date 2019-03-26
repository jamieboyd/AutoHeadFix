#! /usr/bin/python
#-*-coding: utf-8 -*-

from MPR121TouchDetector import TouchDetector
from AHF_LickDetector import AHF_LickDetector
from time import time


class AHF_LickDetector_MPR (AHF_LickDetector, MPR121TouchDetector):
    """
    Lick detector for Auto Head Fix based on MPR121 capacitive touch sensor
    """
    defaultIRQ = 26
    """
    GPIO pin for IRQ signal form lick detector, used for triggering callback
    """
    defaultAddress = 0x5a 
    """
    i2c addresss is 0x5a (90) with address pin tied to ground
    address will be 0x5b (91) with address pin tied to 3v3
    """
    defaultTouchThresh = 8
    defaultUntouchThresh = 4
    """
    Touch thresholds recommended by dirkjan
    """
    defaultTouchChannels = (0,1,2,3)
    """
    number of channels on the mpr121 is 12, but last channel is sum of all channels
    """
    @staticmethod
    def customCallback(channel):
        """
        custom callback 
        """
        AHF_Task.gTask.DataLogger.writeToLogFile(gTask.tag, 'lick', {'chan' : channel}, time())
        newVal = AHF_Task.gTask.Subjects.get(gTask.tag).get('resultsDict').get('LickDetector').get('licks') + 1
        AHF_Task.gTask.Subjects.get(gTask.tag).get('resultsDict').get('LickDetector').update ({'licks' : newVal})


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
        touchThresh = startDict.get ('touchThresh', AHF_LickDetector_MPR.defaultTouchThresh)
        response = input ('Enter 8-bit (0-255) touch threshold value, curently %d: ' % touchThresh)
        if response !+ '':
            touchthresh = int (response)
        unTouchThresh = startDict.get ('unTouchThresh', AHF_LickDetector_MPR.defaultunTouchThresh)
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
        starterDict.update ({'unTouchThresh' : unTouchthresh, 'touchChans' : touchChans})
        return starterDict  


    def setup (self):
        # read dictionary
        self.IRQpin = self.settingsDict.get ('IRQpin')
        self.I2Caddress = self.settingsDict.get ('mprAddress')
        self.touchThresh = self.settingsDict.get ('touchThresh')
        self.unTouchThresh = self.settingsDict.get ('unTouchThresh')
        self.touchChans = self.settingsDict.get ('touchChans')
        # initialize capacitive sensor object
        self.touchDetector = TouchDetector(self.I2Caddress, touchThresh, unTouchThresh)
        self.touchDetector.installCallback (self.IRQpin, self.touchChans, TouchDetector.callbackSetTouch)
        self.touchDetector.addCustomCallback (self.customCallback)

    def newResultsDict (self, starterDict = {}):
        """
        Returns a dictionary with fields, initialized to 0,
        """
        return starterDict.update ({'licks' : starterDict.get ('licks', 0)})

    def clearResultsDict(self, resultsDict):
        """
        Clears values in the results dictionary, for daily totals of licks on all channels. Could be extended to per channel data
        """
        resultsDict.update ({'licks' : 0})

    def setdown (self):
        self.touchDetector.removeCallback (self.IRQpin)
        del self.touchDetector

    def getTouches (self):
        """
        gets touches from mpr121
        """
        return self.touchDetector.touched ()


    def startLogging (self):
        """
        tells the AHF_LickDetectorCallback to log touches in shell and file (if present)
        """



    def stopLogging (self):
        """
        tells the AHF_LickDetectorCallback to stop logging touches in shell and file (if present)
        """
        self.isLogging = False


    def zeroLickCount (self):
        """
        Zeros the selected list of channels in the global array of licks per channel that the callback function updates.
        Use it to count licks, by zeroing selected channels, then checking the values in the array
        """
        for chan in range (0, self.numTouchChannels):
            self.lickArray [chan] = 0


    def getLickCount (self, chanList):
        """
        takes a list of channels and returns a list where each member is the number of licks for that channel in the global array
        call zeroLickCount, wait a while for some licks, then call getLickCount
        """
        global gLickArray
        returnList = []
        for chan in chanList:
            returnList.append (self.lickArray[chan])
        return returnList

 

    def resetDetector (self):
        """
        Calls MPR121 reset function. Should rarely need to do this? This could be of use in resetting baseline untouched values.
        """
        self.mpr121._reset ()



    def waitForLick (self, timeOut_secs, startFromZero=False):
        """
        Waits for a lick on any channel. Returns channel that was touched, or 0 if timeout expires with no touch,
        or -1 if startFromZero was True and the detector was touched for entire time
         """
        endTime = time() + timeOut_secs
        if self.prevTouches == 0: # no touches now, wait for first touch, or timeout expiry
            while self.prevTouches ==0 and time() < endTime:
                sleep (0.05)
            return self.prevTouches
        else: #touches already registered
            if not startFromZero: # we are done already
                return self.prevTouches
            else: # we first wait till there are no touches, or time has expired
                while self.prevTouches > 0 and time() < endTime:
                    sleep (0.05)
                if time() > endTime: # touched till timeout expired
                    return -1
                else: # now wait for touch or til timeout expires
                    while self.prevTouches == 0 and time() < endTime:
                        sleep (0.05)
                    return self.prevTouches # will be the channel touched, or 0 if no touches till timeout expires

    
 
    def hardwareTest (self):
        from math import log
        """
        tests the lick detector, designed to be called by the hardware tester,can modify IRQ pin in hardware settings
        If asked to change IRQ pin, also resets the detector
        """
        self.startLogging ()
        lickError = 0
        self.zeroLickCount()
        print ('\nTo pass the test, start with lick spout untouched and touch spout within 10 seconds....')
        lick = self.waitForLick (10, True)
        if lick >= 1:
            print ('Touch registerd on channel %d' % int (log (lick, 2))) # will round to highest number channel reporting touched
        else:
            if lick == -1:
                rStr= 'Touches were registered the whole 10 seconds: '
            else:
                rStr= 'No Touches were detected in 10 seconds: '
            inputStr=input (rStr + '\nDo you want to change the lick detetctor settings? :') 
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                self.setdown()
                self.settingsDict = self.config_user_get (self.settingsDict)
                self.setup() 
            else:
                self.resetDetector()
       
