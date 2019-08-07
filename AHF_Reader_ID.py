#! /usr/bin/python
#-*-coding: utf-8 -*-
from time import time, sleep
from _thread import start_new_thread, interrupt_main
import threading
import RPi.GPIO as GPIO

import RFIDTagReader
import AHF_Task
from AHF_Reader import AHF_Reader

class AHF_Reader_ID (AHF_Reader):

    TIME_OUT_SECS = 0.05
    DO_CHECK_SUM = True

    defaultPort = '/dev/ttyUSB0'
    defaultPin = 7
    defaultChamberTimeLimit = 600
    graceTime = 5

    gStillThere = False
    gInChamberTimeLimit = 0.0
    isChecking = True

    @staticmethod
    def customCallback(channel):
        """
        callback sets tag value in global reference to task object.
        DO NOT START CALLBACK BEFORE TASK IS INITED
        also logs entries in TagReader results dict for the mouse the tag corresponds to
        """
        if GPIO.input (channel) == GPIO.HIGH: # tag just entered
            print("hello")
            try:
                tag = RFIDTagReader.globalReader.readTag ()
                print(tag)
                if AHF_Task.gTask.Subjects.get(tag) is not None:
                    AHF_Task.gTask.tag = tag
                    AHF_Task.gTask.DataLogger.writeToLogFile(AHF_Task.gTask.tag, 'entry', None, time())
                    AHF_Task.gTask.entryTime = time()
                    AHF_Reader_ID.stillThere = True
                    start_new_thread (AHF_Reader_ID.timeInChamberThread,(time () + AHF_Reader_ID.gInChamberTimeLimit,))
                    # newVal = AHF_Task.gTask.Subjects.get(AHF_Task.gTask.tag).get('resultsDict').get('TagReader').get('entries')
                    # newVal = newVal + 1
                    # AHF_Task.gTask.Subjects.get(AHF_Task.gTask.tag).get('resultsDict').get('TagReader').update ({'entries' : newVal})
                    pass
                else:
                    if tag != 0:
                        raise Exception('There are no fresh mice allowed, and this is a fresh mouse')
            except Exception as e:
                print(str(e))
            finally:
                RFIDTagReader.globalReader.clearBuffer()
        else: # tag just left
            AHF_Task.gTask.DataLogger.writeToLogFile(AHF_Task.gTask.tag, 'exit', None, time())
            AHF_Task.gTask.tag = 0
            RFIDTagReader.globalReader.clearBuffer()
            AHF_Reader_ID.stillThere = False

    def constantCheck (self, channel):
        while AHF_Reader_ID.isChecking:
            try:
                if GPIO.input(channel) == GPIO.HIGH:
                    try:
                        tag = self.readTag()
                        if AHF_Task.gTask.Subjects.get(tag) is not None:
                            AHF_Task.gTask.tag = tag
                            AHF_Task.gTask.DataLogger.writeToLogFile(AHF_Task.gTask.tag, 'entry', None, time())
                            AHF_Task.gTask.entryTime = time()
                            AHF_Reader_ID.stillThere = True
                            start_new_thread (AHF_Reader_ID.timeInChamberThread,(time () + AHF_Reader_ID.gInChamberTimeLimit,))
                        else:
                            if tag != 0:
                                raise Exception('There are no fresh mice allowed, and this is a fresh mouse')
                    except Exception as e:
                        print(str(e))
                    finally:
                        self.tagReader.clearBuffer()
                else:
                    #sleep(AHF_Reader_ID.graceTime)
                    if self.task.tag != 0 and not self.task.contact:
                        AHF_Task.gTask.DataLogger.writeToLogFile(AHF_Task.gTask.tag, 'exit', None, time())
                        AHF_Task.gTask.tag = 0
                        self.tagReader.clearBuffer()
                        AHF_Reader_ID.stillThere = False
            except Exception as e:
                break

    @staticmethod
    def timeInChamberThread (sleepEndTime):
        while AHF_Reader_ID.stillThere and (time () < sleepEndTime):
            sleep (0.1)
        if AHF_Reader_ID.stillThere:
            stuckMouse = AHF_Task.gTask.tag
            AHF_Task.gTask.inChamberLimitExceeded = True
            AHF_Task.gTask.headFixer.releaseMouse ()
            AHF_Task.gTask.AHF_BrainLight.offForStim ()
            if hasattr (AHF_Task.gTask, 'Notifer'):
                Notifier = AHF_Task.gTask.Notifier
                Notifier.notifyStuck (stuckMouse, cageID, (time() - AHF_Task.gTask.entryTime), True)
                # wait for mouse to leave chamber
                while AHF_Task.gTask.tag == stuckMouse:
                    sleep (0.1)
                if hasattr (AHF_Task.gTask, 'Notifer'):
                    Notifier.notifyStuck (stuckMouse, cageID, (time() - AHF_Task.gTask.entryTime), False)
                AHF_Task.gTask.inChamberLimitExceeded = False


    @staticmethod
    def about ():
        return 'ID Innovations RFID-Tag Reader on a serial port with GPIO Tag-in-Range Pin'

    @staticmethod
    def config_user_get (starterDict = {}):
        serialPort = starterDict.get('serialPort', AHF_Reader_ID.defaultPort)
        response = input ('Enter port used by tag reader, dev/serial0 if conected to Pi serial port, or dev/ttyUSB0 if connected to a USB breakout, currently %s :' % serialPort)
        if response != '':
            serialPort = response
        TIRpin = starterDict.get('TIRpin', AHF_Reader_ID.defaultPin)
        response = input ('Enter the GPIO pin connected to the Tag-In-Range pin of the Tag Reader, currently %s :' % TIRpin)
        if response != '':
            TIRpin = int (response)
        inChamberTimeLimit = starterDict.get ('inChamberTimeLimit', AHF_Reader_ID.defaultChamberTimeLimit)
        response = input('Enter in-Chamber duration limit, in minutes, before stopping head-fix trials, currently {:.2f}: '.format(inChamberTimeLimit/60))
        if response != '':
            inChamberTimeLimit = int(inChamberTimeLimit * 60)
        starterDict.update({'serialPort' : serialPort, 'TIRpin' : TIRpin, 'inChamberTimeLimit' : inChamberTimeLimit})
        return starterDict

    def newResultsDict (self, starterDict = {}):
        starterDict.update({'entries' : starterDict.get ('entries', 0)})
        return starterDict

    def clearResultsDict(self, resultsDict):
        resultsDict.update({'entries' : 0})

    def setup (self):
        self.serialPort = self.settingsDict.get('serialPort')
        self.TIRpin = self.settingsDict.get('TIRpin')
        self.tagReader =RFIDTagReader.TagReader (self.serialPort, doChecksum = AHF_Reader_ID.DO_CHECK_SUM, timeOutSecs = AHF_Reader_ID.TIME_OUT_SECS, kind='ID')
        self.isLogging = False
        AHF_Reader_ID.gStillThere = False
        AHF_Reader_ID.gInChamberTimeLimit = self.settingsDict.get ('inChamberTimeLimit')

    def setdown (self):
        if self.isLogging:
            self.stopLogging()
        del self.tagReader

    def readTag (self):
        try:
            return self.tagReader.readTag ()
        except ValueError:
            return 0
    def startLogging (self):
        if not self.isLogging:
#            self.tagReader.installCallback (self.TIRpin)
            GPIO.setup (self.TIRpin, GPIO.IN)
            AHF_Reader_ID.isChecking = True
            self.checkThread = threading.Thread(target=self.constantCheck, args=(self.TIRpin,), daemon = True).start()
            self.isLogging = True

    def stopLogging (self):
        if self.isLogging:
#            self.tagReader.removeCallback()
 #           GPIO.remove_event_detect (self.TIRpin)
            AHF_Reader_ID.isChecking = False
            self.isLogging = True

    def hardwareTest (self):
        wasLogging = self.isLogging
        if wasLogging:
            self.stopLogging()
        print ('Monitoring RFID Reader for next 10 seconds....')
        lastTag = -1
        startTime = time()
        GPIO.setup (self.TIRpin, GPIO.IN)
        printed = False
        while time () < startTime + 10:
            try:
                thisTag = self.readTag ()
                if GPIO.input (self.TIRpin) == GPIO.HIGH:
                    printed = False
                    if thisTag != 0:
                        print ('Tag value is now %d.' % thisTag)
                else:
                    if not printed:
                        print('No Tag in Range')
                        printed = True
            except Exception as e:
                print (str(e))
            sleep (AHF_Reader_ID.TIME_OUT_SECS)
        result = input ('Do you wish to edit Tag Reader settings?')
        returnValue = False
        if result [0] == 'y' or result [0] == 'Y':
            self.setdown ()
            self.settingsDict = self.config_user_get (self.settingsDict)
            self.setup ()
            returnValue = True
        if wasLogging:
            self.startLogging()

        return returnValue
