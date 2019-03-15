#! /usr/bin/python3
#-*-coding: utf-8 -*-


from AHF_Subjects import AHF_Subjects

import AHF_ClassAndDictUtils as CAD

class AHF_Subjects_mice (AHF_Subjects):
    """
    class for the mice, as experimental subjects.Contains a dictionary where key id IDtag, and value is a dicitonary
    of configuration information for corresponding mouse.
    Dictionaries from Stimulator, 1 for results, stimResults, and 1 for parameters, stimParams
    Dictionary from HeadFixer, either headFix% or headFix type (loose, strong, a scale from 1 -8)
    Dictionary from Rewarder, task and entry reward size, max entry rewards, daily reward totals
    """
    freshMiceDefault = False
    loadConfigsDefault = True
    
    @staticmethod
    def about():
        return 'Contains configuration data and results for a group of mice as experimental subjects in Auto Head Fix'

    @staticmethod
    def config_user_get (starterDict = {}):
        freshMiceAllowed = starterDict.get('freshMiceAllowed', freshMiceDefault)
        tempInput = input ('Ignore mice whose RFID tags are not present in mouse configuration data, currently {:}? :'.format (freshMiceAllowed))
        if tempInput [0] == 'y' or tempInput [0] == 'Y':
            freshMiceAllowed = False
        else:
            freshMiceAllowed = True
        loadConfigs =  starterDict.get('loadMiceConfigs', loadConfigsDefault)
        tempInput = input ('Load mice configurations from Data logger, currently {:}? :'.format(loadConfigs))
        if tempInput [0] == 'y' or tempInput [0] == 'Y':
            loadConfigs = True
        else:
            loadConfigs =  False
        starterDict.update ({'loadMiceConfigs' : loadConfigs, 'freshMiceAllowed' : freshMiceAllowed})
        return starterDict


    def setup():
        self.current = None # reference to current mouse in the array, the one that is in the experimental tube
        self.freshMiceAllowed = self.settingsDict.get ('freshMiceAllowed')
        self.loadConfigs = self.settingsDict.get ('loadMiceConfig')
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
        A Generator function that generates a dictionary of settings each of the mice in turn. Sample function call
        for mouse in myMice.generator():
        """
        for key, value in self.miceDict.items():
            yield (key, value)
                

    def newResultsDict (self):
        mDict = {'HeadFixerDict' : self.task.HeadFixerDict, 'HeadFixerResults' : self.task.HeadFixer.newResultsDict (self.HeadFixer)}
        mDict.update ({'RewarderDict' : self.task.RewarderDict, 'RewarderResults' : self.task.Rewarder.newResultsDict (self.Rewarder)})
        mDict.update ({'StimulatorDict' : self.task.StimulatorDict, 'StimulatorResults' : self.task.Stimulator.newResultsDict (self.Rewarder)})
        return mDict


    def clearResultsDict(self, resultsDict):
        for key, value in self.miceDict.items():
            self.task.HeadFixer.clearResultsDict (value)
            self.task.Rewarder.clearResultsDict (value)
            self.task.Stimulator.clearResultsDict (value)
    
    def get (self, IDnum):
        """
        returns a reference to the dictionary for the mouse with given IDtag. if the mouse tag is not found, makes a new dictionary 
        if fresh mice can be added, else returns an empty dicitonary if fresh mice are to be ignored
        """
        if not IDnum in self.miceDict.keys and self.freshMiceAllowed:
            self.miceDict.update ({IDnum, self.newResultsDict()})
        return self.miceDict.get (IDnum, {})



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
