#! /usr/bin/python
#-*-coding: utf-8 -*-

from time import time, sleep
from datetime import datetime


from MPR121TouchDetector import TouchDetector
from AHF_LickDetector import AHF_LickDetector


class AHF_LickDetector_MPR (AHF_LickDetector):
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
    numTouchChannels = 12
    """
    number of channels on the mpr121 is 12
    """
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
            
        starterDict.update ({'mprAddress' : mprAddress, 'IRQpin' : pin})
        return starterDict  

    def setup (self):
        # read dictionary
        self.pin = self.settingsDict.get ('IRQpin')
        self.address = self.settingsDict.get ('mprAddress')
        # initialize capacitive sensor object and start it up
        if hasattr (self.task, 'DataLogger'):
            self.dataLogger = self.task.DataLogger
        else:
            self.dataLogger = None
        self.isLogging = False
        self.lickArray = array ('i', [0]*self.numTouchChannels)
        # set up global lick detector with callback
        global gLickDetector
        gLickDetector = self
         # set up IRQ interrupt function. GPIO.setmode should alreay have been called
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect (self.pin, GPIO.FALLING)
        GPIO.add_event_callback (self.pin, MPR_Callback)        


    def setdown (self):
        GPIO.remove_event_detect (self.pin)
        GPIO.cleanup (self.pin)
        del self.mpr121

    def getTouches (self):
        """
        gets touches from mpr121
        """
        return self.prevTouches


    def startLogging (self):
        """
        tells the AHF_LickDetectorCallback to log touches in shell and file (if present)
        """
        if self.dataLogger is not None:
            self.isLogging = True


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
       


def main():
    serialPort = '/dev/serial0'
    #serialPort = '/dev/ttyUSB0'
    tag_in_range_pin=21
    lick_IRQ_pin = 26
    import RPi.GPIO as GPIO
    import RFIDTagReader
    from time import sleep
    GPIO.setmode (GPIO.BCM)
    tagReader = RFIDTagReader.TagReader(serialPort, True, timeOutSecs = 0.05, kind='ID')
    tagReader.installCallBack (tag_in_range_pin)
    logger = Simple_Logger (None)
    lickDetetctor = LickDetector (lick_IRQ_pin, logger)
    lickDetetctor.zeroLickCount ([0,1])
    print ('Waiting for licks...')
    lickDetetctor.startLogging()
    #sleep (20)
    for i in range (0,10):
        while RFIDTagReader.globalTag == 0:
            sleep (0.02)
        mouse = RFIDTagReader.globalTag
        logger.writeToLogFile (mouse, 'Mouse Entry')
        while RFIDTagReader.globalTag != 0:
            sleep (0.02)
        logger.writeToLogFile (mouse, 'Mouse Exit')
    lickDetetctor.stopLogging()
    print (lickDetetctor.getLickCount ([0,1]), ' licks in 10 entries')


if __name__ == '__main__':
    main()
