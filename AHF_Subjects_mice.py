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
    loadConfigsDefault = 'generate_json'
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
        tempInput = input ('Load specific mice configurations from AHF_mice_settings.json file.\n'
                           'type F to generate a fillable json file,\n'
                           'type G to use the GUI to generate the json file'
                           'type P to provide a correct json file or \n'
                           'type D if you have all information in the Database, currently {:}? :'.format(loadConfigs))
        if tempInput [0] == 'd' or tempInput [0] == 'D':
            loadConfigs = "database"
        elif tempInput [0] == 'p' or tempInput [0] == 'P':
            loadConfigs = 'provide_json'
        elif tempInput [0] == 'g' or tempInput [0] == 'G':
            loadConfigs = 'Gui_json'
        else:
            loadConfigs = 'fillable_json'

        inChamberTimeLimit = starterDict.get ('inChamberTimeLimit',AHF_Subjects_mice.inChamberTimeLimitDefault)
        response = input('Enter in-Chamber duration limit, in minutes, before stopping head-fix trials, currently {:.2f}: '.format(inChamberTimeLimit/60))
        if response != '':
            inChamberTimeLimit = int(inChamberTimeLimit * 60)

        starterDict.update ({'loadMiceConfigs' : loadConfigs, 'freshMiceAllowed' : freshMiceAllowed, 'inChamberTimeLimit' : inChamberTimeLimit})

        return starterDict

    def depth(self,d, level=0):
        if not isinstance(d, dict) or not d:
            return level
        return min(self.depth(d[k], level + 1) for k in d)

    def check_miceDict(self,starterDict={}):
        if len(starterDict)==0:
            check= False
        else:
            depth = self.depth(starterDict)
            if depth != 3:
                check = False
            else:
                for key in starterDict.keys():
                    y = list(starterDict.get(key).keys())
                    if sorted(self.settingsTuple) != sorted(y):
                        check = False
                        break
                    else:
                        check = True
        if check == False:
            print("your Json could not be confirmed, please fill out the AHF_fillable_mice_settings.json")



        headFixerDict = self.task.HeadFixer.config_user_subject_get(starterDict.get('HeadFixer'))



    def setup(self):
        # hardware.json subject.json

        self.settingsTuple = ('HeadFixer', 'Rewarder', 'Stimulator')
        self.freshMiceAllowed = self.settingsDict.get ('freshMiceAllowed')
        self.loadConfigs = self.settingsDict.get ('loadMiceConfig')
        self.propHeadFix = self.settingsDict.get ('propHeadFix')
        self.inChamberTimeLimit = self.settingsDict.get ('inChamberTimeLimit')
        self.miceDict = {}
        if self.loadConfigs == "database" and hasattr (self.task, 'DataLogger'): # try to load mice configuration from dataLogger
            dataLogger=self.task.DataLogger
            for configTuple in dataLogger.configGenerator ("current_subjects"):
                self.miceDict.update (configTuple)
        elif self.loadConfigs == "provide_json" or  self.loadConfigs == 'fillable_json': # only accept 2 options for filenames: mice_settings.json or fillable_mice_settings.json and check if the format is correct
            if self.loadConfigs == 'fillable_json':
                # provide a fillable json with the base default values and wait for the user to edit them

            try:
                try:
                    self.miceDict = CAD.File_to_dict('mice', 'settings','.jsn')
                except:
                    self.miceDict = CAD.File_to_dict('fillable_mice', 'settings', '.jsn')
                self.check_miceDict(self.miceDict) #TODO
            except ValueError as e:
                print('Unable to open and fully load task configuration:' + str(e))
                fileErr = True
                    # TODO add config user subject get

        if len(self.miceDict) > 0:
            for tag in self.miceDict.keys():
                for source in self.miceDict.get(tag):
                    self.task.DataLogger.storeConfig(tag, self.miceDict.get(tag).get(source), source)
                #TODO save configs in DB when finished

    def setdown (self):
        # TODO: Finish this
        pass
    def show (self, IDnum = 0):
        """
        Prints out attributes for subject with given IDNum. If IDNum is 0, prints attributes for all subjects in pool.
        The attributes will be defined by subclass, results provided by stimulator, etc. Returns true if IDNum was found in
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
        
    
    def add(self, IDnum, dataDict={}):

        """
        Adds a new subject to the pool of subjects, initializing subject fields with data from a dictionary
        returns True if subject was added, false if subjet with IDnum already exists in subject pool
        """
        if IDnum == 't' or IDnum == 'T':
            tag = 0
            while tag == 0:
                tag = self.task.TagReader.readTag()
                sleep(0.1)

        elif IDnum == 'a' or IDnum == 'A':
            tag = int(input('Enter the RFID tag for new mouse: '))
            notes = input(
            'add any notes that might be used by the program to adjust the task, like excitatory,inhibitory,control,...')
        elif isinstance(IDnum, int):
            tag = IDnum

        for source in self.settingsTuple:
            reference = getattr(self.task,source)
            dataDict = reference.config_user_subject_get(dataDict)
        if not IDnum in self.miceDict.keys:
            self.miceDict.update ({tag, dataDict})
            notes = dataDict.get("Notes")
            self.task.DataLogger.saveNewMouse(tag,notes)


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


    def individualSettings (self, starterDict={}):
        starterDict.update ({'propHeadFix' : self.propHeadFix})
        # TODO datalogger


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

    def subjectSettings(self):
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
            inputStr += 'J to create a Json file for subject settings from Database\n'
            event = input (inputStr)
            tag = 0
            if event == 'p' or event == 'P': # print mice stats
                #self.showMice ()
                # TODO make queries and think of strategy
            elif event == 'r' or event == 'R': # remove a mouse
                mice = self.task.DataLogger.getMice()
                tag = input ('Mice currently known to be in the cage : {}.\n'
                             'Enter the RFID tag of the mouse to be removed: '.format(str(mice)))
                reason = input('Why do you want to retire the mouse (e.g. participation, window, health, finished): ')
                if tag != '' and tag in mice:
                    self.task.DataLogger.retireMouse(tag,reason)
                    mice = self.task.DataLogger.getMice()
                    print('mice now in cage: {}'.format(str(mice)))
                else:
                    print("wrong tag")
            elif event == 'j' or event == 'J':
                default = input ('Use CURRENT settings for each mouse for Json? (otherwise DEFAULT settings are used')
                if default[0] == 'y' or default[0] == 'Y':
                    settings = "current_subjects"
                else:
                    settings = "default_subjects"
                jsonDict = {}
                for config in self.task.DataLogger.configGenerator(settings):
                    jsonDict.update(config)
                if len(jsonDict) > 0:
                    nameStr = input('Chose a filename. Your file will be automatically named: AHF_mice_filename.json')
                    configFile = 'AHF_mice' + nameStr + '.json'
                    with open(configFile, 'w') as fp:
                        fp.write(json.dumps(jsonDict, separators=('\n', '='), sort_keys=True, skipkeys=True))
                        fp.close()
                        uid = pwd.getpwnam('pi').pw_uid
                        gid = grp.getgrnam('pi').gr_gid
                        os.chown(configFile, uid, gid)  # we may run as root for pi PWM, so we need to explicitly set ownership
                    # TODO check this, ask jamie
            else: # other two choices are for adding a mouse by RFID Tag, either reading from Tag Reader, or typing it
                self.add(event) #TODO

    def hardwareTest(self):
        from time import sleep
        while True:
            inputStr = '\n change the following variables. \nEnter:\n'
            inputStr += '0 leave settings'
            inputStr += '1 inChamberTimeLimit'
            inputStr += '2 freshMiceAllowed'
            inputStr += '3 store Dictionary in Database'
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
                result = input()
                #TODO
        self.setup()
from AHF_Task import Task

from AHF_TagReader import AHF_TagReader
from AHF_Base import AHF_Base
