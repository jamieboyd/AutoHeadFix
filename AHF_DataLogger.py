#! /usr/bin/python
#-*-coding: utf-8 -*-
from os import path, makedirs, chown
from pwd import getpwnam
from grp import getgrnam
from time import time, localtime,timezone
from datetime import datetime
import RFIDTagReader

class AHF_DataLogger (object):
    PSEUDO_MUTEX =0
    def __init__ (self, task):
        self.cageID = str(task.get ('cageID'))
        self.dataPath = task.get('dataPath')
        self.logFP = None
        self.statsFP = None
        self.setDateStr ()
        self.makeDayFolderPath ()
        self.makeLogFile ()
        

    def newDay (self, mice):
        self.writeToLogFile ('SeshEnd')
        if self.logFP is not None:
            self.logFP.close()
        if self.statsFP is not None:
            self.statsFP.close()
        self.setDateStr () 
        self.makeDayFolderPath()
        self.makeLogFile ()
        self.makeQuickStatsFile (mice)


    def setDateStr (self):
        dateTimeStruct = localtime()
        self.dateStr= str (dateTimeStruct.tm_year) + (str (dateTimeStruct.tm_mon)).zfill(2) + (str (dateTimeStruct.tm_mday)).zfill(2)


    def makeDayFolderPath (self):
        """
        Makes data folders for a day's data,including movies, log file, and quick stats file

        Format: dayFolder = cageSettings.dataPath + cageSettings.cageID + YYYMMMDD
        within which will be /Videos and /TextFiles

        """
        self.dayFolderPath = self.dataPath + self.dateStr + '/' + self.cageID + '/'
        if not path.exists(self.dayFolderPath):
            makedirs(self.dayFolderPath, mode=0o777, exist_ok=True)
            makedirs(self.dayFolderPath + 'TextFiles/', mode=0o777, exist_ok=True)
            makedirs(self.dayFolderPath + 'Videos/', mode=0o777, exist_ok=True)
            uid = getpwnam ('pi').pw_uid
            gid = getgrnam ('pi').gr_gid
            chown (self.dayFolderPath, uid, gid)
            chown (self.dayFolderPath + 'TextFiles/', uid, gid)
            chown (self.dayFolderPath + 'Videos/', uid, gid)

    def makeLogFile (self):
        """
        open a new text log file for today, or open an exisiting text file with 'a' for append
        """
        self.logFilePath = self.dayFolderPath + 'TextFiles/headFix_' + self.cageID + '_' + self.dateStr + '.txt'
        self.logFP = open(self.logFilePath, 'a')
        uid = getpwnam ('pi').pw_uid
        gid = getgrnam ('pi').gr_gid
        chown (self.logFilePath, uid, gid)
        self.writeToLogFile ('SeshStart')

        
    def writeToLogFile(self, tag, event):
        """
        Writes the time and type of each event to a text log file, and also to the shell

        Format of the output string: tag     time_epoch or datetime       event
        The computer-parsable time_epoch is printed to the log file and user-friendly datetime is printed to the shell
        :param tag: the tag of mouse, usually from RFIDTagreader.globalTag
        :param event: the type of event to be printed, entry, exit, reward, etc.
        returns: nothing
        """
        tag = RFIDTagReader.globalTag
        while AHF_DataLogger.PSEUDO_MUTEX ==1:
            sleep (0.01)
        AHF_DataLogger.PSEUDO_MUTEX = 1
        if event == 'SeshStart' or event == 'SeshEnd':
            tag = 0
        outPutStr = '{:013}'.format(tag)
        logOutPutStr = outPutStr + '\t' + '{:.2f}'.format (time ())  + '\t' + event +  '\t' + datetime.fromtimestamp (int (time())).isoformat (' ')
        printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
        print (printOutPutStr)
        if self.logFP is not None:
            self.logFP.write(logOutPutStr + '\n')
            self.logFP.flush()
        AHF_DataLogger.PSEUDO_MUTEX = 0

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
        if self.logFP is not None:
            self.logFP.close()
            self.statsFP.close()
