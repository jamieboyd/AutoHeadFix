#! /usr/bin/python
#-*-coding: utf-8 -*-
from time import time, sleep
from AHF_TagReader import AHF_TagReader

import RFIDTagReader

class AHF_TagReader_ID (AHF_TagReader):

    TIME_OUT_SECS = 0.05
    DO_CHECK_SUM = True
    
    @staticmethod
    def about ():
        return 'ID Innovations RFID-Tag Reader on a serial port with GPIO Tag-in-Range Pin'

    @staticmethod
    def config_user_get (paramDict = {}):
        serialPort = paramDict.get('serialPort', '/dev/serial0')
        response = input ('Enter port used by tag reader, dev/serial0 if conected to Pi serial port, or dev/ttyUSB0 if connected to a USB breakout, currently %s :' % serialPort)
        if response != '':
            serialPort = response
        TIRpin = paramDict.get('TIRpin', 21)
        response = input ('Enter the GPIO pin connected to the Tag-In-Range pin of the Tag Reader, currently %s :' % TIRpin)
        if response != '':
            TIRPin = int (response)
        paramDict.update({'serialPort' : serialPort, 'TIRpin' : TIRpin})
        return paramDict

    def __init__ (self, RFIDdict):
        self.RFIDdict = RFIDdict
        self.setup ()

    def setup (self):
        self.serialPort = self.RFIDdict.get('serialPort')
        self.TIRpin = self.RFIDdict.get('TIRpin')
        self.tagReader =RFIDTagReader.TagReader (self.serialPort, doChecksum = AHF_TagReader_ID.DO_CHECK_SUM, timeOutSecs = AHF_TagReader_ID.TIME_OUT_SECS, kind='ID')
        self.tagReader.installCallBack (self.TIRpin)

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
            self.RFIDdict.update(AHF_TagReader_ID.config_user_get (self.RFIDdict))
            self.setup ()
