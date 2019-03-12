#! /usr/bin/python
#-*-coding: utf-8 -*-
from os import path, makedirs, chown
from pwd import getpwnam
from grp import getgrnam
from time import time, localtime,timezone
from datetime import datetime

class AHF_DataLogger_text (AHF_DataLogger):
    """
    Simple text-based data logger modified from the original Auto Head Fix code
    makes a new text file for each day, saved in default data path. 
    
    Mouse data is stored in a specified folder, also as text files, one text file per mouse
    containing JSON formatted configuration and performance data. These files will opened and
    updated after each exit from the experimental tube, in case the program needs to be restarted
    
    
    """
    PSEUDO_MUTEX =0
    """
    The class field PSEUDO_MUTEX helps prevent print statements from different places in the code (main vs
    callbacks) from executing at the same time, which leads to garbled output. Unlike a real mutex, execution
    of the thread is not halted while waiting on the PSEUDO_MUTEX, hence the loops with calls to sleep to
    allow the other threads of execution to continue while waiting for the mutex to be free. Also, read/write
    to the PSEUDO_MUTEX is not atomic; one thread may read PSEUDO_MUTEX as 0, and set it to 1, but in the
    interval between reading and writing to PSEUDO_MUTEX,another thread may have read PSEUDO_MUTEX as 0 and
    both threads think they have the mutex
    """
    defaultCage = 'cage1'
    defaultDataPath='/home/pi/Documents/'
    defaultConfigPath = '/home/pi/Documents/MiceConfig'
    
    @staticmethod
    def about ():
        return 'Simple text-based data logger that prints mouse id, time, event type, and event dictionary to a text file, and to the shell.'

    @staticmethod
    def config_user_get (starterDict = {}):
        # cage ID
        cageID = starterDict.get('cageID', AHF_DataLogger_text.defaultCage)
        response = input('Enter a name for the cage ID (currently %s): ' & cageID)
        if reponse != '':
            cageID = response
        # data path 
        dataPath = starterDict.get('dataPath', AHF_DataLogger_text.defaultDataPath)
        response = input ('Enter the path to the directory where the data will be saved (currently %s): ' % dataPath)
        if reponse != '':
            dataPath = response
        if not dataPath.endswith('/'):
            dataPath += '/'
        # config path
        configPath = starterDict.get('mouseConfigPath', AHF_DataLogger_text.defaultConfigPath)
        response = input ('Enter the path to the directory from which to load and store mouse configuration (currently %s): ' % configPath)
        if reponse != '':
            configPath = response
        # update and return dict
        starterDict.update ({'cageID' : cageID, 'dataPath' : dataPath, 'mouseConfigPath' : configPath})
        return starterDict

        
    def setup (self):
        self.cageID = self.settingsDict.get ('cageID')
        self.dataPath = self.settingsDict.get('dataPath')
        self.configPath = self.settingsDict.get('mouseConfigPath') 
        self.logFP = None # reference to log file that will be created
        self.textFilePath = self.dataPath + 'TextFiles/'
        if not path.exists(self.textFilePath):
            uid = getpwnam ('pi').pw_uid
            gid = getgrnam ('pi').gr_gid
            if not path.exists(self.dataPath):
                makedirs(self.dataPath, mode=0o777, exist_ok=True)
                chown (self.dataPath, uid, gid)
            makedirs(self.textFilePath, mode=0o777, exist_ok=True)
            chown (self.textFilePath, uid, gid)
        self.setDateStr ()
        self.makeLogFile ()

    
    def setdown (self):
        if self.logFP is not None:
            self.logFP.close()


    def newDay (self, mice):
        self.writeToLogFile (0, 'SeshEnd', None, time())
        if self.logFP is not None:
            self.logFP.close()

        self.setDateStr () 
        self.makeLogFile ()
        self.makeQuickStatsFile (mice)
    

    def writeToLogFile(self, tag, eventKind, eventDict, timeStamp):
        """
        Writes the time and type of each event to a text log file, and also to the shell

        Format of the output string: tag     time_epoch or datetime       event
        The computer-parsable time_epoch is printed to the log file and user-friendly datetime is printed to the shell
        :param tag: the tag of mouse, usually from RFIDTagreader.globalTag
        :param eventKind: the type of event to be printed, entry, exit, reward, etc.
        :param eventDict: a dictionary containing data about the event (may be None if no associated data) 
        returns: nothing
        """
        if eventKind == 'SeshStart' or eventKind == 'SeshEnd':
            tag = 0
            eventDict = None
        FileOutputStr = '{:013}\t{:s}\t{:s}\t{:.2f}'.format(tag, eventKind, eventDict, timeStamp)
        LogOutputStr = '{:013}\t{:s}\t{:s}\t{:s}\n'.format (tag, eventKind, eventDict, datetime.fromtimestamp (int (timeStamp)).isoformat (' '))
        while AHF_DataLogger.PSEUDO_MUTEX ==1:
            sleep (0.01)
        AHF_DataLogger.PSEUDO_MUTEX = 1
        print (LogOutputStr)
        if self.logFP is not None:
            self.logFP.write(FileOutputStr)
            self.logFP.flush()
        AHF_DataLogger.PSEUDO_MUTEX = 0
            

    def setDateStr (self):
        dateTimeStruct = localtime()
        self.dateStr='{:04}{:02}{:02}'.format (dateTimeStruct.tm_year, dateTimeStruct.tm_mon, dateTimeStruct.tm_mday)



    def makeQuickStatsFile (self, mice):
        """
        makes a new quickStats file for today, or opens an existing file to append.
        
        QuickStats file contains daily totals of rewards and headFixes for each mouse
        :param expSettings: experiment-specific settings, everything you need to know is stored in this object
        :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
        :param mice: the array of mice objects for this cage
    """
        self.statsFilePath = self.dayFolderPath + 'TextFiles/quickStats_' + self.cageID + '_' + self.dateStr + '.txt'
        if path.exists(self.statsFilePath):
            self.statsFP = open(self.statsFilePath, 'r+')
            if mice is not None:
                mice.addMiceFromFile(self.statsFP)
                mice.show()
        else:
            self.statsFP = open(self.statsFilePath, 'w')
            self.statsFP.write('Mouse_ID\tentries\tent_rew\thfixes\thf_rew\n')
            self.statsFP.close()
            self.statsFP = open(self.statsFilePath, 'r+')
            uid = getpwnam ('pi').pw_uid
            gid = getgrnam ('pi').gr_gid
            chown (self.statsFilePath, uid, gid)


    def updateStats (self, numMice):
        """ Updates the quick stats text file after every exit, mostly for the benefit of folks logged in remotely
        :param statsFP: file pointer to the stats file
        :param mice: the array of mouse objects
        returns:nothing
        """
        pos = self.mouse.arrayPos
        self.statsFP.seek (39 + 38 * pos) # calculate this mouse pos, skipping the 39 char header
        # we are in the right place in the file and new and existing values are zero-padded to the same length, so overwriting should work
        outPutStr = '{:013}'.format(self.mouse.tag) + "\t" +  '{:05}'.format(self.mouse.entries)
        outPutStr += "\t" +  '{:05}'.format(self.mouse.entranceRewards) + "\t" + '{:05}'.format(self.mouse.headFixes)
        outPutStr +=  "\t" + '{:05}'.format(self.mouse.headFixRewards) + "\n"
        self.statsFP.write (outPutStr)
        self.statsFP.flush()
        self.statsFP.seek (39 + 38 * numMice) # leave file position at end of file so when we quit, nothing is truncated

    def addMouseToStats (self, newMouse, numMice):
         # add a blank line to the quik stats file
        if self.statsFP is not None:
            self.statsFP.seek (39 + 38 * numMice)
            outPutStr = '{:013}'.format(int (newMouse.tag)) + "\t" +  '{:05}'.format(0) + "\t" +  '{:05}'.format(0) + "\t"
            outPutStr += '{:05}'.format(0) + "\t" + '{:05}'.format(0) + "\n"
            self.statsFP.write (outPutStr)
            self.statsFP.flush()

    def __del__ (self):
        self.writeToLogFile ('SeshEnd')
        self.setdown()
