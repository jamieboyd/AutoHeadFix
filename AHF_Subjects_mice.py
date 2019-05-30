#! /usr/bin/python3
#-*-coding: utf-8 -*-


from AHF_Subjects import AHF_Subjects
import AHF_ClassAndDictUtils as CAD
import json
import os
import pwd
import grp

class AHF_Subjects_mice (AHF_Subjects):
    """
    class for the mice, as experimental subjects. Contains a dictionary where key id IDtag, and value is a dictionary
    of configuration information for corresponding mouse.
    {mouseid1:{settingsDict:{},resultsDict{}}, mouseid2:{settingsDict:{},resultsDict{}}}
    Dictionaries from Stimulator, 1 for results, stimResults, and 1 for parameters, stimParams
    Dictionary from HeadFixer, either headFix% or headFix type (loose, strong, a scale from 1 -8)
    Dictionary from Rewarder, task and entry reward size, max entry rewards, daily reward totals
    """
    freshMiceDefault = False
    loadConfigsDefault = True
    propHeadFixDefault = 1
    skeddadleTimeDefault =2
    inChamberTimeLimitDefault = 300 #seconds
    headFixTimeDefault = 40 #seconds


    @staticmethod
    def about():
        return 'Contains configuration data and results for a group of mice as experimental subjects in Auto Head Fix'

    @staticmethod
    def config_user_get (starterDict = {}):
        freshMiceAllowed = starterDict.get('freshMiceAllowed', AHF_Subjects_mice.freshMiceDefault)
        tempInput = input ('Ignore mice whose RFID tags are not present in mouse configuration data, currently {:}? :'.format (freshMiceAllowed))
        if tempInput [0] == 'y' or tempInput [0] == 'Y':
            freshMiceAllowed = False
        else:
            freshMiceAllowed = True
        loadConfigs =  starterDict.get('loadMiceConfigs', AHF_Subjects_mice.loadConfigsDefault)
        tempInput = input ('Load mice configurations from Data logger, currently {:}? :'.format(loadConfigs))
        if tempInput [0] == 'y' or tempInput [0] == 'Y':
            loadConfigs = True
        else:
            loadConfigs =  False

        inChamberTimeLimit = starterDict.get ('inChamberTimeLimit',AHF_Subjects_mice.inChamberTimeLimitDefault)
        response = input('Enter in-Chamber duration limit, in minutes, before stopping head-fix trials, currently {:.2f}: '.format(inChamberTimeLimit/60))
        if response != '':
            inChamberTimeLimit = int(inChamberTimeLimit * 60)
        starterDict.update ({'loadMiceConfigs' : loadConfigs, 'freshMiceAllowed' : freshMiceAllowed, 'inChamberTimeLimit' : inChamberTimeLimit})

        return starterDict


    def setup(self):
        settingsTuple = ('HeadFixer', 'Rewarder', 'Stimulator')
        self.freshMiceAllowed = self.settingsDict.get ('freshMiceAllowed')
        self.loadConfigs = self.settingsDict.get ('loadMiceConfig')
        self.propHeadFix = self.settingsDict.get ('propHeadFix')
        self.skeddadleTime = self.settingsDict.get ('skeddadleTime')
        self.inChamberTimeLimit = self.settingsDict.get ('inChamberTimeLimit')
        self.miceDict = {}
        if self.loadConfigs and hasattr (self.task, 'DataLogger'): # try to load mice configuration from dataLogger
            dataLogger=self.task.DataLogger
            for configTuple in dataLogger.configGenerator ():
                self.miceDict.update ({configTuple[0] : configTuple[1]})

    def setdown (self):
        # TODO: Finish this
        pass
    def show (self, IDnum = 0):
        """
        Prints out attributes for subject with given IDNum. If IDNum is 0, prints attributes for all subjects in pool.
        The attributes will be defined by subclass, results provided by stimulator, etc. Retyrns true if IDNum was found in
        pool, else False
        """
        pass


    def check (self, IDnum):
        """
        returns 1 if IDnum is already in subjects, 0 if IDnum is not in subjects but is elgible to be added, returns -1 if IDnum is not elgible to be added
        """
        if IDnum in self.miceDict.keys:
            return 1
        elif self.freshMiceAllowed:
            return 0
        else:
            return -1
        
    
    def add(self, IDnum, dataDict):

        """
        Adds a new subject to the pool of subjects, initializing subject fields with data from a dictionary
        returns True if subject was added, false if subjet with IDnum already exists in subject pool
        """
        if not IDnum in self.miceDict.keys:
            self.miceDict.update ({IDnum, dataDict})
            self.task.DataLogger.saveNewMouse(IDnum)
            return True
        else:
            return False


    def remove (self, IDnum):
        if IDnum in self.miceDict.keys:
            self.miceDict.pop(IDnum)
            self.task.DataLogger.retireMouse(IDnum)
            return True
        else:
            return False


    def userEdit (self):
        """
        Allows user interaction to add and remove subjects, print out and edit individual configuration
        """
        CAD.Edit_dict (self.miceDict, 'Mice')


    def generator(self):
        """
        A Generator function that generates a (tagID, dictionary) tuple for each of the mice in turn.
        Sample function call: for mouse in myMice.generator():
        """
        for item in self.miceDict.items():
            yield item


    def newSubjectDict (self, starterDict = {}):
        """
        New dictionary made for each individual mouse, dictionaries for headFixer, rewarder, Stmiulator, and
        TagReader
        A separate dictionary tracks individual settings, which over-ride global settings
        """
        settingsDict = starterDict.get ('settingsDict', {})
        settingsDict.update ({'HeadFixer' : self.task.HeadFixer.settingsDict })
        settingsDict.update ({'Rewarder' : self.task.Rewarder.settingsDict })
        settingsDict.update ({'Stimulator' : self.task.Stimulator.settingsDict })
        return {'settingsDict': settingsDict}

    def clearResultsDict(self, resultsDict):
        """
        Clears results for HeadFixer, Rewarder, Stimulator, and results tracked in Mice class
        """
        for key, value in self.miceDict.get (resultsDict).items():
            self.task.HeadFixer.clearResultsDict (value)
            self.task.Rewarder.clearResultsDict (value)
            self.task.Stimulator.clearResultsDict (value)
            self.task.TagReader.clearResultsDict
            # TODO datalogger save settings and notify that dict is cleared


    def individualSettings (self, starterDict={}):
        starterDict.update ({'propHeadFix' : self.propHeadFix})
        # TODO datalogger save settings and notify that dict is cleared


    def get (self, IDnum):
        """
        returns a reference to the dictionary for the mouse with given IDtag. if the mouse tag is not found, makes a new dictionary
        if fresh mice can be added, else returns an empty dicitonary if fresh mice are to be ignored
        """
        if (not self.miceDict or not IDnum in self.miceDict) and self.freshMiceAllowed:
            self.miceDict[IDnum]= self.newSubjectDict()
        return self.miceDict.get (IDnum, None)

    def get_all (self):
        return self.miceDict

    def animalSettings(self):
        """
        Allows user to add mice to file, maybe use TagReader, give initial values to paramaters
        """
        from time import sleep
        while True:
            inputStr = '\n************** Mouse Configuration ********************\nEnter:\n'
            inputStr += 'A to add a mouse, by its RFID Tag\n'
            inputStr += 'T to read a tag from the Tag Reader and add that mouse\n'
            inputStr += 'P to print current daily stats for all mice\n'
            inputStr += 'R to remove a mouse from the list, by RFID Tag\n: '
            inputStr += 'J to create a Json file for animal settings'
            event = input (inputStr)
            tag = 0
            if event == 'p' or event == 'P': # print mice stats
                self.showMice ()
            elif event == 'r' or event == 'R': # remove a mouse
                mice = self.task.DataLogger.getMice()
                tag = input ('Mice currently known to be in the cage : {}.\n'
                             'Enter the RFID tag of the mouse to be removed: '.format(str(mice)))
                reason = input('Why do you want to retire the mouse (e.g. participation, window, health, finished): ')
                self.task.DataLogger.retireMouse(tag,reason)
                mice = self.task.DataLogger.getMice()
                print('mice now in cage: {}'.format(str(mice)))
            elif event == 'j' or event == 'J':
                default = input ('load current settings for each mouse? (otherwise default settings are used')
                if default[0] == 'y' or default[0] == 'Y':
                    nameStr = "current_mice"
                else:
                    nameStr = "default_mice"
                jsonDict = {}
                for config in self.task.DataLogger.configGenerator(nameStr):
                    jsonDict.update(config)
                if len(jsonDict) > 0:
                    configFile = 'AHF_' + nameStr + '_settings_' + self.cageID + ".json"
                with open(configFile, 'w') as fp:
                    fp.write(json.dumps(jsonDict, separators=('\n', '='), sort_keys=True, skipkeys=True))
                    fp.close()
                    uid = pwd.getpwnam('pi').pw_uid
                    gid = grp.getgrnam('pi').gr_gid
                    os.chown(configFile, uid, gid)  # we may run as root for pi PWM, so we need to explicitly set ownership
            else: # other two choices are for adding a mouse by RFID Tag, either reading from Tag Reader, or typing it
                if event == 't' or event == 'T':
                    tag = 0
                    while tag == 0:
                        tag = self.task.TagReader.readTag()
                        sleep (0.1)
                elif event == 'a' or event == 'A':
                    tag = int(input ('Enter the RFID tag for new mouse: '))
                self.task.DataLogger.saveNewMouse(tag)

    def hardwareTest(self):
        from time import sleep
        while True:
            inputStr = '\n change the following variables. \nEnter:\n'
            inputStr += '0 leave settings'
            inputStr += '1 inChamberTimeLimit'
            inputStr += '2 freshMiceAllowed'
            inputStr += '3 skeddadle Time'
            event = input(inputStr)
            if event == 0:
                break
            if event == '2':
                result = input('Ignore mice whose RFID tags are not present in mouse configuration data, currently {:}? :'.format(self.freshMiceAllowed))
                if result[0] == 'y' or result[0] == 'Y':
                    self.settingsDict.update({'freshMiceAllowed': False})
                else:
                    self.settingsDict.update({'freshMiceAllowed': True})
            if event == '1':
                result = input('Enter in-Chamber duration limit, in minutes, before stopping head-fix trials, currently {:.2f}: '.format(self.inChamberTimeLimit / 60))
                if result != '':
                    self.settingsDict.update({'inChamberTimeLimit': int(result * 60)})
            if event == '3':
                result = input('Change the skedaddle time for mice, currently {:}: '.format(self.skeddadleTime))
                if result != '':
                    self.settingsDict.update({'skeddadleTime': int(result)})
        self.setup()
from AHF_Task import Task

from AHF_TagReader import AHF_TagReader
from AHF_Base import AHF_Base
