#! /usr/bin/python
#-*-coding: utf-8 -*-
from time import time, sleep
from AHF_TagReader import AHF_TagReader

import RFIDTagReader

class AHF_TagReader_ID (AHF_TagReader):

    TIME_OUT_SECS = 0.05
    DO_CHECK_SUM = True

    defaultPort = '/dev/serial0'
    defaultPin = 21
    
    @staticmethod
    def about ():
        return 'ID Innovations RFID-Tag Reader on a serial port with GPIO Tag-in-Range Pin'

    @staticmethod
    def config_user_get (starterDict = {}):
        serialPort = starterDict.get('serialPort', AHF_TagReader_ID.defaultPort)
        response = input ('Enter port used by tag reader, dev/serial0 if conected to Pi serial port, or dev/ttyUSB0 if connected to a USB breakout, currently %s :' % serialPort)
        if response != '':
            serialPort = response
        TIRpin = starterDict.get('TIRpin', AHF_TagReader_ID.defaultPin)
        response = input ('Enter the GPIO pin connected to the Tag-In-Range pin of the Tag Reader, currently %s :' % TIRpin)
        if response != '':
            TIRpin = int (response)
        starterDict.update({'serialPort' : serialPort, 'TIRpin' : TIRpin})
        return starterDict

    def setup (self):
        self.serialPort = self.settingsDict.get('serialPort')
        self.TIRpin = self.settingsDict.get('TIRpin')
        self.tagReader =RFIDTagReader.TagReader (self.serialPort, doChecksum = AHF_TagReader_ID.DO_CHECK_SUM, timeOutSecs = AHF_TagReader_ID.TIME_OUT_SECS, kind='ID')
        self.tagReader.installCallBack (self.TIRpin)

    def setdown (self):
        del self.tagReader
        

    def readTag (self):
        return RFIDTagReader.globalTag

    def hardwareTest (self):
        print ('Monitoring RFID Reader for next 10 seconds....')
        lastTag = -1
        startTime = time()
        while time () < startTime + 10:
            thisTag = self.readTag ()
            if thisTag != lastTag:
                if thisTag == 0:
                    print ('No Tag in Range.')
                else:
                    print ('Tag value is now %d.' % thisTag)
                lastTag = thisTag
            sleep (AHF_TagReader_ID.TIME_OUT_SECS)
        result = input ('Do you wish to edit Tag Reader settings?')
        if result [0] == 'y' or result [0] == 'Y':
            self.setdown ()
            self.settingsDict = self.config_user_get (self.settingsDict)
            self.setup ()
