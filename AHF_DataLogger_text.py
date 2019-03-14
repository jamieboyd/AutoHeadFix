#! /usr/bin/python
#-*-coding: utf-8 -*-
from os import path, makedirs, chown, listdir
from pwd import getpwnam
from grp import getgrnam
from time import time, localtime,timezone
from datetime import datetime
import AHF_ClassAndDictUtils as CAD
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

    def setdown (self):
        """
        Writes session end and closes log file
        """
        if self.logFP is not None:
            self.writeToLogFile (0, 'SeshEnd', None, time())
            self.logFP.close()

    def loadAllMiceData (self):
        """
        Each mouse configuration file has config data for a single mouse. This function loads mice for all
        the files in the folder and returns a list of mice objects
        """
        fileList = []
        miceList = []
        for fname in listdir(self.configPath):
            if fname.startswith ('AHF_mouse_') and fname.endswith ('.jsn'):
                fileList.append (fname)
        for fname in fileList:
            tagStr = fname[10:len (fname)-4]
            new_mouse = Mouse (int(tagStr))
            CAD.File_to_obj_fields ('mouse', tagStr, '.jsn', new_mouse, dir = self.configPath)
        return miceList

    def loadMouseData (self, mouse):
        """
        loads data from corresponding json text file, overwriting any data existing in the mouse object
        """
        CAD.File_to_obj_fields ('mouse', '{:013}'.format(mouse.tag), '.jsn', mouse, dir = self.configPath)

    def saveMouseData (self, mouse):
        """
        saves data to corresponding json text file, overwriting old file
        """
        CAD.Obj_fields_to_file (mouse, 'mouse', '{:013}'.format(mouse.tag), '.jsn', dir = self.configPath)


    def makeQuickStatsFile (self, mice):
        """
        makes a quickStats file for today's results.
        
        QuickStats file contains daily totals of rewards and headFixes for each mouse
        :param expSettings: experiment-specific settings, everything you need to know is stored in this object
        :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
        :param mice: the array of mice objects for this cage
        """
        statsFilePath = self.statsPath + 'quickStats_' + self.cageID + '_' + self.dateStr + '.txt'
        statsFP = open(statsFilePath, 'w')
        statsFP.write('Mouse_ID\tentries\tent_rew\thfixes\thf_rew')
        if mice is not None:
            keyList = self.task.Stimulator.MousePrecis (mice.)
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
        LogOutputStr = '{:013}\t{:s}\t{:s}\t{:s}\n'.format (tag, eventKind, eventDict, datetime.fromtimestamp (int (timeStamp)).isoformat (' '))
        while AHF_DataLogger.PSEUDO_MUTEX ==1:
            sleep (0.01)
        AHF_DataLogger.PSEUDO_MUTEX = 1
        print (LogOutputStr)
        AHF_DataLogger.PSEUDO_MUTEX = 0
        if self.logFP is not None:
            FileOutputStr = '{:013}\t{:s}\t{:s}\t{:.2f}'.format(tag, eventKind, eventDict, timeStamp)                                 
            self.logFP.write(FileOutputStr)
            self.logFP.flush()

    def setDateStr (self):
        dateTimeStruct = localtime()
        self.dateStr='{:04}{:02}{:02}'.format (dateTimeStruct.tm_year, dateTimeStruct.tm_mon, dateTimeStruct.tm_mday)





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
