#! /usr/bin/python
#-*-coding: utf-8 -*-
from os import path, makedirs, chown, listdir
from pwd import getpwnam
from grp import getgrnam
from time import time, localtime,timezone, sleep
from datetime import datetime
import AHF_ClassAndDictUtils as CAD
from AHF_DataLogger import AHF_DataLogger
class AHF_DataLogger_text (AHF_DataLogger):
    """
    Simple text-based data logger modified from the original Auto Head Fix code
    makes a new text logfile for each day, saved in default data path.

    Mouse data is stored in a specified folder, also as text files, one text file per mouse
    containing JSON formatted configuration and performance data. These files will opened and
    updated after each exit from the experimental tube, in case the program needs to be restarted
    The file name for each mouse contains RFID tag 0-padded to 13 spaces: AHF_mouse_1234567890123.jsn

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
    defaultConfigPath = '/home/pi/Documents/MiceConfig/'

    @staticmethod
    def about ():
        return 'Simple text-based data logger that prints mouse id, time, event type, and event dictionary to a text file, and to the shell.'

    @staticmethod
    def config_user_get (starterDict = {}):
        # cage ID
        cageID = starterDict.get('cageID', AHF_DataLogger_text.defaultCage)
        response = input('Enter a name for the cage ID (currently %s): ' % cageID)

        if response != '':
            cageID = response
        # data path
        dataPath = starterDict.get('dataPath', AHF_DataLogger_text.defaultDataPath)
        response = input ('Enter the path to the directory where the data will be saved (currently %s): ' % dataPath)
        if response != '':
            dataPath = response
        if not dataPath.endswith('/'):
            dataPath += '/'
        # config path
        configPath = starterDict.get('mouseConfigPath', AHF_DataLogger_text.defaultConfigPath)
        response = input ('Enter the path to the directory from which to load and store mouse configuration (currently %s): ' % configPath)
        if response != '':
            configPath = response
        # update and return dict
        starterDict.update ({'cageID' : cageID, 'dataPath' : dataPath, 'mouseConfigPath' : configPath})
        return starterDict

    def setup (self):
        """
        copies settings, creates folders for data and stats, creates initial log file and writes start session
                    dataPath          path to data folder
                      _|_
                     /   \
              logPath   statsPath      subfolders within data folder
                 |         |
             logFilePath  statsFilePath paths to individual files within corresponding subfolders
        """
        self.cageID = self.settingsDict.get ('cageID')
        self.dataPath = self.settingsDict.get('dataPath')
        self.configPath = self.settingsDict.get('mouseConfigPath')
        self.logFP = None # reference to log file that will be created
        self.dataPath = self.settingsDict.get('dataPath')
        self.configPath = self.settingsDict.get('mouseConfigPath')
        self.logFP = None # reference to log file that will be created
        self.logPath = self.dataPath + 'LogFiles/' # path to the folder containing log files
        self.logFilePath = '' # path to the log file
        self.statsPath = self.dataPath + 'QuickStats/'
        self.uid = getpwnam ('pi').pw_uid
        self.gid = getgrnam ('pi').gr_gid
        # data path
        if not path.exists(self.dataPath):
            makedirs(self.dataPath, mode=0o777, exist_ok=True)
            chown (self.dataPath, self.uid, self.gid)
        # logPath, folder in data path
        if not path.exists(self.logPath):
            makedirs(self.logPath, mode=0o777, exist_ok=True)
            chown (self.logPath, self.uid, self.gid)
        # stats path, a different folder in data path
        if not path.exists(self.statsPath):
            makedirs(self.statsPath, mode=0o777, exist_ok=True)
            chown (self.statsPath, self.uid, self.gid)
        # mouseConFigPath can be anywhere, not obliged to be in data path
        if not path.exists(self.configPath):
            makedirs(self.configPath, mode=0o777, exist_ok=True)
            chown (self.configPath, self.uid, self.gid)
        self.setDateStr ()  # makes a string for today's date, used in file names
        self.makeLogFile () # makes and opens a file for today's data inside logFilePath folder, sets logFP
        self.writeToLogFile (0, 'SeshStart', None, time())

    def hardwareTest (self):
        """
        Tests functionality, gives user a chance to change settings
        """
        pass

    def setdown (self):
        """
        Writes session end and closes log file
        """
        if getattr(self, 'logFP', None) is not None:
            self.writeToLogFile (0, 'SeshEnd', None, time())
            self.logFP.close()
        mice = self.task.Subjects.get_all()
        for tag, mouse in mice.items():
            self.storeConfig(tag, mouse)

    def configGenerator (self):
        """
        Each configuration file has config data for a single subject. This function loads data
        from all of them in turn, and returning each as a a tuple of (tagID, dictionary)
        """
        for fname in listdir(self.configPath):
            if fname.startswith ('AHF_mouse_') and fname.endswith ('.jsn'):
                tagStr = fname[10:len (fname)-4]
                yield (int(tagStr), CAD.File_to_dict('mouse', tagStr, '.jsn', dir = self.configPath))

    def getConfigData (self, tag):
        """
        returns saved dictionary for given tag
        """
        return CAD.File_to_dict ('mouse', '{:013}'.format(tag), '.jsn', dir = self.configPath)


    def storeConfig (self, tag, configDict, source = ""):
        """
        saves data to corresponding json text file, overwriting old file
        """
        CAD.Dict_to_file (configDict, 'mouse', '{:013}'.format(tag), '.jsn', dir = self.configPath)

    def saveNewMouse (self, tag, note, dictionary = {}):
        self.storeConfig(tag, dictionary)
        self.writeToLogFile(tag, "NewMouse", dictionary, time())

    def getMice (self):
        mice = []
        for config in self.configGenerator():
            mice.append(config[0])
        return mice

    def retireMouse (self, tag, reason):
        CAD.Remove_file('mouse', '{:013}'.format(tag), '.jsn', dir = self.configPath)
        self.writeToLogFile(tag, "Retirement", {'reason': reason}, time())

    def newDay (self, mice):
        self.writeToLogFile (0, 'SeshEnd', None, time())
        if self.logFP is not None:
            self.logFP.close()
        self.setDateStr ()
        self.makeLogFile ()
        self.makeQuickStatsFile (mice)


    def makeLogFile (self):
        """
        open a new text log file for today, or open an exisiting text file with 'a' for append
        """
        try:
            self.logFilePath = self.logPath + 'headFix_' + self.cageID + '_' + self.dateStr + '.txt'
            self.logFP = open(self.logFilePath, 'a')
            chown (self.logFilePath, self.uid, self.gid)
        except Exception as e:
                print ("Error maing log file\n", str(e))

    def readFromLogFile(self, tag, index):
        pass

    def writeToLogFile(self, tag, eventKind, eventDict, timeStamp, toShellOrFile=3):
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
        LogOutputStr = '{:013}\t{:s}\t{:s}\t{:s}\n'.format (tag, eventKind, str(eventDict), datetime.fromtimestamp (int (timeStamp)).isoformat (' '))
        while AHF_DataLogger_text.PSEUDO_MUTEX ==1:
            sleep (0.01)
        AHF_DataLogger_text.PSEUDO_MUTEX = 1
        print (LogOutputStr)
        AHF_DataLogger_text.PSEUDO_MUTEX = 0
        if getattr(self, 'logFP', None) is not None and self.task.logToFile: # logMouse is set to False for test mice, or unknown mice
            FileOutputStr = '{:013}\t{:s}\t{:s}\t{:.2f}\n'.format(tag, eventKind, str(eventDict), timeStamp)
            self.logFP.write(FileOutputStr)
            self.logFP.flush()


    def setDateStr (self):
        """
        Sets the string corresponding to todays date that is used when making files
        """
        dateTimeStruct = localtime()
        self.dateStr='{:04}{:02}{:02}'.format (dateTimeStruct.tm_year, dateTimeStruct.tm_mon, dateTimeStruct.tm_mday)


    def makeQuickStatsFile (self, mice):
        """
        makes a quickStats file for today's results.

        QuickStats file contains daily totals of rewards and headFixes for each mouse
        """
        statsFilePath = self.statsPath + 'quickStats_' + self.cageID + '_' + self.dateStr + '.txt'
        statsFP = open(statsFilePath, 'w')
        statsFP.write('Mouse_ID\tentries\tent_rew\thfixes\thf_rew')
        if mice is not None:
            keyList = self.task.Stimulator.MousePrecis (mice)
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

    def __del__ (self):
        self.writeToLogFile (0, 'SeshEnd', None, time())
        self.setdown()
