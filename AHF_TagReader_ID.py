#! /usr/bin/python
#-*-coding: utf-8 -*-
from time import time, sleep

import RFIDTagReader
import AHF_Task
from AHF_TagReader import AHF_TagReader

class AHF_TagReader_ID (AHF_TagReader):

    TIME_OUT_SECS = 0.05
    DO_CHECK_SUM = True

    defaultPort = '/dev/serial0'
    defaultPin = 21

    @staticmethod
    def customCallback(channel):
        """
        callback sets tag value in global reference to task object.
        DO NOT START CALLBACK BEFORE TASK IS INITED
        also logs entries in TagReader results dict for the mouse the tag corresponds to
        """
        if GPIO.input (channel) == GPIO.HIGH: # tag just entered
            try:
                AHF_Task.gTask.tag = RFIDTagReader.globalReader.readTag ()
                AHF_Task.gTask.DataLogger.writeToLogFile(gTask.tag, 'entry', None, time())
                newVal = AHF_Task.gTask.Subjects.get(gTask.tag).get('resultsDict').get('TagReader').get('entries') + 1
                AHF_Task.gTask.Subjects.get(gTask.tag).get('resultsDict').get('TagReader').update ({'entries' : newVal})
            except Exception as e:
                AHF_Task.gTask.tag =0
        else: # tag just left
            AHF_Task.gTask.DataLogger.writeToLogFile(gTask.tag, 'exit', None, time())
            AHF_Task.gTask.tag = 0
            RFIDTagReader.globalReader.clearBuffer()
 
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

    def newResultsDict (self, starterDict = {}):
        return starterDict.update({'entries' : starterDict.get ('entries', 0)})

    def clearResultsDict(self, resultsDict):
        resultsDict.update({'entries' : 0})
        
    def setup (self):
        self.serialPort = self.settingsDict.get('serialPort')
        self.TIRpin = self.settingsDict.get('TIRpin')
        self.tagReader =RFIDTagReader.TagReader (self.serialPort, doChecksum = AHF_TagReader_ID.DO_CHECK_SUM, timeOutSecs = AHF_TagReader_ID.TIME_OUT_SECS, kind='ID')
        self.isLogging = False

    def setdown (self):
        if self.isLogging:
            self.stopLogging()
        del self.tagReader
        
    def readTag (self):
        return self.tagReader.readTag ()

    def startLogging (self):
        if not self.isLogging:
            self.tagReader.installCallBack (self.TIRpin, callBackFunc = AHF_TagReader_ID.customCallback)
            self.isLogging = True

    def stopLogging (self):
        if self.isLogging:
            self.tagReader.removeCallback()
            GPIO.remove_event_detect (self.tag_in_range_pin)
            self.isLogging = False
        
    def hardwareTest (self):
        wasLogging = self.isLogging
        if wasLogging:
            self.stopLogging()
        self.stopLogging()
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
        if wasLogging:
            self.startLogging()
