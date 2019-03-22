#! /usr/bin/python3
#-*-coding: utf-8 -*-


from AHF_Subjects import AHF_Subjects

import AHF_ClassAndDictUtils as CAD

class AHF_Subjects_mice (AHF_Subjects):
    """
    class for the mice, as experimental subjects.Contains a dictionary where key id IDtag, and value is a dicitonary
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
    inChamberTimeLimitDefault = 600

    
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
            self.inChamberTimeLimit = int(inChamberTimeLimit * 60)
        starterDict.update ({'loadMiceConfigs' : loadConfigs, 'freshMiceAllowed' : freshMiceAllowed, 'inChamberTimeLimit' : inChamberTimeLimit})
        return starterDict


    def setup():
        resultsTuple = ('HeadFixer', 'Rewarder', 'Stimulator', 'entries') # results tuple defines dictionaries for subjects we will read from and write results to
        settingsTuple= ('HeadFixer', 'Rewarder', 'Stimulator')
        self.freshMiceAllowed = self.settingsDict.get ('freshMiceAllowed')
        self.loadConfigs = self.settingsDict.get ('loadMiceConfig')
        self.propHeadFix = self.settingsDict.get ('propHeadFix')
        self.skeddadleTime = self.settingsDict.get ('skeddadleTime')
        self.inChamberTimeLimit = self.settingsDict.get ('inChamberTimeLimit')
        self.miceDict = {}
        if self.loadConfigs and hasattr (self.task, 'DataLogger'): # try to load mice configuration from dataLogger
            dataLogger=self.task.DataLogger
            for configTuple in DataLogger.configGenerator ():
                self.miceDict.update ({configTuple[0] : configTuple[1]})
            

    def add (self, IDnum, dataDict):
        """
        Adds a new subject to the pool of subjects, initializing subject fields with data from a dictionary
        returns True if subject was added, false if subjet with IDnum already exists in sibject pool
        """
        if not IDnum in self.miceDict.keys:
            self.miceDict.update ({IDnum, dataDict})
            return True
        else:
            return False

    
    def remove (self, IDnum):
        if IDnum in self.miceDict.keys:
            self.miceDict.pop(IDnum)
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
                

    def newSubjectDict (starterDict = {}):
        """
        New dictionary made for each individual mouse, dictionaries for headFixer, rewarder, Stmiulator, and
        TagReader
        A separate dictionary tracks individual settings, which over-ride global settings
        """
        resultsDict = starterDict.get ('resultsDict', {})
        resultsDict.update ({'HeadFixer' : self.task.HeadFixer.newResultsDict ()})
        resultsDict.update ({'Rewarder' : self.task.Rewarder.newResultsDict ()})
        resultsDict.update ({'Stimulator' : self.task.Stimulator.newResultsDict ()})
        resultsDict.update ({'TagReader' : self.task.TagReader.newResultsDict ()})
        settingsDict = starterDict.get ('settingsDict', {})
        settingsDict.update ({'HeadFixer' : self.task.HeadFixer.settingsDict ()})
        settingsDict.update ({'Rewarder' : self.task.Rewarder.settingsDict ()})
        settingsDict.update ({'Stimulator' : self.task.Stimulator.settingsDict ()})
        return {'resultsDict' : resultsDict, 'settingsDict' : settingsDict)

    def clearResultsDict(self, resultsDict):
        """
        Clears results for HeadFixer, Rewarder, Stimulator, and results tracked in Mice class
        """
        for key, value in self.miceDict.get (resultsDict).items():
            self.task.HeadFixer.clearResultsDict (value)
            self.task.Rewarder.clearResultsDict (value)
            self.task.Stimulator.clearResultsDict (value)
            self.task.TagReader.clearResultsDict
            

    def individualSettings (self, starterDict={}):
        starterDict.update ({'propHeadFix' : self.propHeadFix})
        
        
    
    def get (self, IDnum):
        """
        returns a reference to the dictionary for the mouse with given IDtag. if the mouse tag is not found, makes a new dictionary 
        if fresh mice can be added, else returns an empty dicitonary if fresh mice are to be ignored
        """
        if not IDnum in self.miceDict.keys and self.freshMiceAllowed:
            self.miceDict.update ({IDnum, self.newResultsDict()})
        return self.miceDict.get (IDnum, None)



    def hardwareTest(self):
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
            event = input (inputStr)
            tag = 0
            if event == 'p' or event == 'P': # print mice stats
                self.showMice ()
            elif event == 'r' or event == 'R': # remove a mouse
                tag = input ('Enter the RFID tag of the mouse to be removed: ')
                wasFound = False
                for mouse in self.mouseList:
                    if mouse.tag == tag:
                        self.mouseList.remove (mouse)
                        wasFound = True
                        break
                if not wasFound:
                    print ('Mouse with tag ' + str (tag) + ' was not found.')
            else: # other two choices are for adding a mouse by RFID Tag, either reading from Tag Reader, or typing it
                if event == 't' or event == 'T':
                    tag = 0
                    while tag == 0:
                        tag = self.task.TagReader.readTag()
                        sleep (0.1)
                elif event == 'a' or event == 'A':
                    tag = int(input ('Enter the RFID tag for new mouse: '))
                

     
                
from AHF_Task import Task

from AHF_TagReader import AHF_TagReader
from AHF_Base import AHF_Base
