#! /usr/bin/python
# -*-coding: utf-8 -*-
from os import path, makedirs, chown
from pwd import getpwnam
from grp import getgrnam
from time import time, localtime, timezone
from datetime import datetime


class AHF_DataLogger_mysql(AHF_DataLogger):
    """
    Simple mysql-based data logger modified from the original Auto Head Fix code
    makes a new mysql file for each day, saved in default path.
    """
    PSEUDO_MUTEX = 0
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
    defaultPath = '/home/pi/Documents/'

    @staticmethod
    def about():
        return 'Simple mysql-based data logger that prints mouse id, time, and event to shell and to a mysql file.'

    @staticmethod
    def config_user_get(starterDict={}):
        cageID = starterDict.get('cageID', AHF_DataLogger_mysql.defaultCage)
        response = input('Enter a name for the cage ID (currently %s): ' & cageID)
        if reponse != '':
            cageID = response
        dataPath = starterDict.get('dataPath', AHF_DataLogger_mysql.defaultPath)
        response = input('Enter the path to the directory where the data will be saved (currently %s): ' % dataPath)
        if reponse != '':
            dataPath = response
        starterDict.update({'cageID': cageID, 'dataPath': dataPath})
        return starterDict

    def setup(self):
        self.cageID = self.settingsDict.get('cageID')
        self.dataPath = self.settingsDict.get('dataPath')
        self.logFP = None
        self.setDateStr()
        self.makeDayFolderPath()
        self.makeLogFile()

    def setdown(self):
        if self.logFP is not None:
            self.logFP.close()
        if self.statsFP is not None:
            self.statsFP.close()

    def newDay(self, mice):
        self.writeToLogFile(0, 'SeshEnd')
        if self.logFP is not None:
            self.logFP.close()
        if self.statsFP is not None:
            self.statsFP.close()
        self.setDateStr()
        self.makeDayFolderPath()
        self.makeLogFile()
        self.makeQuickStatsFile(mice)

    def writeToLogFile(self, tag, event, timeStamp):
        """
        Writes the time and type of each event to a mysql log file, and also to the shell

        Format of the output string: tag     time_epoch or datetime       event
        The computer-parsable time_epoch is printed to the log file and user-friendly datetime is printed to the shell
        :param tag: the tag of mouse, usually from RFIDTagreader.globalTag
        :param event: the type of event to be printed, entry, exit, reward, etc.
        returns: nothing
        """
        if event == 'SeshStart' or event == 'SeshEnd':
            tag = 0
        outPutStr = '{:013}'.format(tag)
        logOutPutStr = outPutStr + '\t' + '{:.2f}'.format(time()) + '\t' + event + '\t' + datetime.fromtimestamp(
            int(time())).isoformat(' ')
        printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp(int(time())).isoformat(' ') + '\t' + event
        while AHF_DataLogger.PSEUDO_MUTEX == 1:
            sleep(0.01)
        AHF_DataLogger.PSEUDO_MUTEX = 1
        print(printOutPutStr)
        if self.logFP is not None:
            self.logFP.write(logOutPutStr + '\n')
            self.logFP.flush()
        AHF_DataLogger.PSEUDO_MUTEX = 0

    def setDateStr(self):
        dateTimeStruct = localtime()
        self.dateStr = str(dateTimeStruct.tm_year) + (str(dateTimeStruct.tm_mon)).zfill(2) + (
            str(dateTimeStruct.tm_mday)).zfill(2)

    def makeDayFolderPath(self):
        """
        Makes data folders for a day's data,including movies, log file, and quick stats file

        Format: dayFolder = cageSettings.dataPath + cageSettings.cageID + YYYMMMDD
        within which will be /Videos and /mysqlFiles

        """
        self.dayFolderPath = self.dataPath + self.dateStr + '/' + self.cageID + '/'
        if not path.exists(self.dayFolderPath):
            makedirs(self.dayFolderPath, mode=0o777, exist_ok=True)
            makedirs(self.dayFolderPath + 'mysqlFiles/', mode=0o777, exist_ok=True)
            makedirs(self.dayFolderPath + 'Videos/', mode=0o777, exist_ok=True)
            uid = getpwnam('pi').pw_uid
            gid = getgrnam('pi').gr_gid
            chown(self.dayFolderPath, uid, gid)
            chown(self.dayFolderPath + 'mysqlFiles/', uid, gid)
            chown(self.dayFolderPath + 'Videos/', uid, gid)

    def makeQuickStatsFile(self, mice):
        """
        makes a new quickStats file for today, or opens an existing file to append.

        QuickStats file contains daily totals of rewards and headFixes for each mouse
        :param expSettings: experiment-specific settings, everything you need to know is stored in this object
        :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
        :param mice: the array of mice objects for this cage
    """
        self.statsFilePath = self.dayFolderPath + 'mysqlFiles/quickStats_' + self.cageID + '_' + self.dateStr + '.txt'
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
            uid = getpwnam('pi').pw_uid
            gid = getgrnam('pi').gr_gid
            chown(self.statsFilePath, uid, gid)

    def updateStats(self, numMice):
        """ Updates the quick stats mysql file after every exit, mostly for the benefit of folks logged in remotely
        :param statsFP: file pointer to the stats file
        :param mice: the array of mouse objects
        returns:nothing
        """
        pos = self.mouse.arrayPos
        self.statsFP.seek(39 + 38 * pos)  # calculate this mouse pos, skipping the 39 char header
        # we are in the right place in the file and new and existing values are zero-padded to the same length, so overwriting should work
        outPutStr = '{:013}'.format(self.mouse.tag) + "\t" + '{:05}'.format(self.mouse.entries)
        outPutStr += "\t" + '{:05}'.format(self.mouse.entranceRewards) + "\t" + '{:05}'.format(self.mouse.headFixes)
        outPutStr += "\t" + '{:05}'.format(self.mouse.headFixRewards) + "\n"
        self.statsFP.write(outPutStr)
        self.statsFP.flush()
        self.statsFP.seek(39 + 38 * numMice)  # leave file position at end of file so when we quit, nothing is truncated

    def addMouseToStats(self, newMouse, numMice):
        # add a blank line to the quik stats file
        if self.statsFP is not None:
            self.statsFP.seek(39 + 38 * numMice)
            outPutStr = '{:013}'.format(int(newMouse.tag)) + "\t" + '{:05}'.format(0) + "\t" + '{:05}'.format(0) + "\t"
            outPutStr += '{:05}'.format(0) + "\t" + '{:05}'.format(0) + "\n"
            self.statsFP.write(outPutStr)
            self.statsFP.flush()

    def __del__(self):
        self.writeToLogFile('SeshEnd')
        self.setdown()
