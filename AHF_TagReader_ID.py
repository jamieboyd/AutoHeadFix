#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_TagReader import AHF_TagReader

import RFIDTagReader

class AHF_TagReader_ID (AHF_TagReader):

    gTIME_OUT_SECS = 0.05
    gDO_CHECK_SUM = True
    
    @staticmethod
    def about ():
        return 'ID Innovations RFID-Tag Reader on serial port with GPIO Tag-in-Range Pin'

    @staticmethod
    def config_user_get ():
        serialPort = input ('Enter port used by tag reader, "/dev/serial0\" if conected to Pi serial port, or "/dev/ttyUSB0" if connected to a USB breakout:')
        TIRpin = input ('Enter the GPIO pin connected to the Tag-In-Range pin of the Tag Reader:')
        configDict = {'serialPort' : serialPort, 'TIRpin' : TIRpin}
        return configDict

    def __init__ (self, RFIDdict):
        self.RFIDdict = RFIDdict
        self.serialPort = self.RFIDdict.get('serialPort', '/dev/serial0')
        self.TIRpin = self.RFIDdict.get('TIRpin', 22)
        self.setup ()

    def setup (self):
        self.tagReader =RFIDTagReader.TagReader (self.serialPort, doChecksum = gDO_CHECK_SUM, timeOutSecs = gTIME_OUT_SECS, kind='ID')
        self.tagReader.installCallBack (self.tirPin)

    def readTag (self):
        return RFIDTagReader.globalTag

    def hardwareTest (self):
        pass
