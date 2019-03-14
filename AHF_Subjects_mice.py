#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Subjects import AHF_Subjects

class AHF_Subjects_mice (AHF_Subjects):
    """
    class for the mice, as experimental subjects.Contains an array of Mouse objects, plus a reference to the Task object
    Has an inner class for the mice objects, which is a very basic mouse class with few built-in attributes. But Mice
    objects may have appended attributes as follows:
    Dictionaries from Stimulator, 1 for results, stimResults, and 1 for parameters, stimParams
    Dictionary from HeadFixer, either headFix% or headFix type (loose, strong, a scale from 1 -8)
    Dictionary from Rewarder, task and entry reward size, max entry rewards, daily reward totals
    """
    freshMiceDefault = False
    loadConfigsDefault = True
    
    @staticmethod
    def about():
        return 'Contains configuration and results for mice as experimental subjects in Auto Head Fix'


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
        self.miceList = []
        self.freshMiceAllowed = self.settingsDict.get ('freshMiceAllowed')
        self.loadConfigs = self.settingsDict.get ('loadMiceConfig')
        
        if self.loadConfigs and hasattr (self.task, 'DataLogger'): # try to load mice configuration from dataLogger
            

from AHF_Task import Task
import AHF_ClassAndDictUtils as CAD
from AHF_TagReader import AHF_TagReader
from AHF_Base import AHF_Base
