#! /usr/bin/python3
#-*-coding: utf-8 -*-


from AHF_Subjects import AHF_Subjects
import AHF_ClassAndDictUtils as CAD
import json
import os
import pwd
import grp
from time import sleep

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
    loadConfigsDefault = 'provide_json'
    propHeadFixDefault = 1
    skeddadleTimeDefault =2
    jsonNameDefault = "subjects"
    inChamberTimeLimitDefault = 300 #seconds
    headFixTimeDefault = 40 #seconds


    @staticmethod
    def about():
        return 'Contains configuration data and results for a group of mice as experimental subjects in Auto Head Fix'

    @staticmethod
    def config_user_get (starterDict = {}):

        loadConfigs =  starterDict.get('loadMiceConfigs', AHF_Subjects_mice.loadConfigsDefault)
        jsonName = starterDict.get("jsonName", AHF_Subjects_mice.jsonNameDefault)
        tempInput = input ('Getting subject information:\n'
                           'type P to provide a correct json file or get help creating a new one\n'
                           'type D in case you have all information in the Database and want to use it\n'
                           ' currently {:}? :'.format(loadConfigs))
        if tempInput [0] == 'd' or tempInput [0] == 'D':
            loadConfigs = "database"
        elif tempInput [0] == 'p' or tempInput [0] == 'P':
            loadConfigs = 'provide_json'
            jsonName = input('Chose a FILENAME. Your file will be automatically named: AHF_mice_FILENAME.json (place it in the working directory) Currently {:}' .format(jsonName))
        inChamberTimeLimit = starterDict.get ('inChamberTimeLimit',AHF_Subjects_mice.inChamberTimeLimitDefault)
        response = input('Enter in-Chamber duration limit, in minutes, before stopping head-fix trials, currently {:.2f}: '.format(inChamberTimeLimit/60))
        if response != '':
            inChamberTimeLimit = int(inChamberTimeLimit * 60)

        starterDict.update ({'loadMiceConfigs' : loadConfigs, 'inChamberTimeLimit' : inChamberTimeLimit, "jsonName": jsonName})
        return starterDict

    def setup(self):
        # hardware.json subject.json

        self.settingsTuple = ('HeadFixer', 'Rewarder', 'Stimulator')
        self.loadConfigs = self.settingsDict.get('loadMiceConfigs')
        self.jsonName = self.settingsDict.get('jsonName')
        self.inChamberTimeLimit = self.settingsDict.get('inChamberTimeLimit')
        self.miceDict = {}
        self.resultsDict = {}
        if self.loadConfigs == "database" and hasattr(self.task,
                                                      'DataLogger'):  # try to load mice configuration from dataLogger
            dataLogger = self.task.DataLogger
            for configTuple in dataLogger.configGenerator("current_subjects"):
                self.miceDict.update(configTuple)
        elif self.loadConfigs == "provide_json":  #check file, if not existing or not correct provide a fillable json, then update miceDict when user is ready
            try:
                self.miceDict = CAD.File_to_dict('mice', self.jsonName, '.jsn')
                if self.check_miceDict(self.miceDict) == False:
                    raise Exception('Could not confirm dictionary')
            except Exception as e:
                print('Unable to open and fully load task configuration, we will create a fillable json for you.\n'
                      'Edit the contents to your liking, then COPY the file to your filename. DO NOT rename.')
                self.create_fillable_json()
            while self.check_miceDict(self.miceDict) == False:
                input('could not load json, please edit and try again. Press enter when done')

            for tag in self.miceDict.keys():
                for source in self.miceDict.get(tag):
                    self.task.DataLogger.storeConfig(tag, self.miceDict.get(tag).get(source), source)
    def create_fillable_json(self):
        tempInput = input('A for adding a mouse with the tag number \n'
                          'T for using the RFID Tag reader ')
        moreMice =True
        while moreMice:
            self.add(tempInput[0])
            stillmore = input('add another mouse? Y or N')
            if stillmore[0] == "n" or stillmore[0] == "N":
                moreMice = False
        print(self.miceDict)            
        CAD.Dict_to_file (self.miceDict, "mice_fillable", self.jsonName, ".jsn")
        input('Please edit the values now. Press enter when done')
        self.miceDict = CAD.File_to_dict('mice', self.jsonName, '.jsn')


    def depth(self,d, level=0):
        if not isinstance(d, dict) or not d:
            return level
        return min(self.depth(d[k], level + 1) for k in d)


    def check_miceDict(self,starterDict={}):
        check= True
        if len(starterDict) > 0 and self.depth(starterDict) == 3:
            print(starterDict.keys())
            for mouse in starterDict.keys():
                mice_list = list(starterDict.get(mouse).keys())
                if sorted(self.settingsTuple) == sorted(mice_list):
                    for source in self.settingsTuple:
                        reference = getattr(self.task,source)
                        sourceDict = reference.config_subject_get()
                        if set(sourceDict.keys()) != set(starterDict.get(mouse).get(source).keys()):
                            check = False
                else:
                    print("mid")
                    check = False
        else:
            check = False
        if check == False:
            print("your Json could not be confirmed, please fill out the AHF_fillable_mice_settings.json")
        return check

    def setdown (self):
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
        else:
            return -1


    def add(self, IDnum, dataDict={},default=True):

        """
        Adds a new subject to the pool of subjects, initializing subject fields with data from a dictionary
        returns True if subject was added, false if subjet with IDnum already exists in subject pool
        """
        if IDnum == 't' or IDnum == 'T':
            tag = 0
            while tag == 0:
                tag = self.task.Reader.readTag()
                sleep(0.1)

        elif IDnum == 'a' or IDnum == 'A':
            tag = int(input('Enter the RFID tag for new mouse: '))
        elif isinstance(IDnum, int):
            tag = IDnum
        for source in self.settingsTuple:
            reference = getattr(self.task,source)
            if default:
                sourceDict = reference.config_subject_get(dataDict.get(source,{}))
            else:
                sourceDict = reference.config_user_subject_get(dataDict.get(source,{}))
            dataDict.update({source:sourceDict})
        if not tag in self.miceDict.keys():
            self.miceDict.update ({tag: dataDict})
            note = ''
            self.task.DataLogger.saveNewMouse(tag,note, self.miceDict.get(tag))


    def remove (self, IDnum):
        if IDnum in self.miceDict.keys:
            self.miceDict.pop(IDnum)
            self.task.DataLogger.retireMouse(IDnum, "")
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



    def individualSettings (self, starterDict={}):
        starterDict.update ({'propHeadFix' : self.propHeadFix})
        # TODO datalogger


    def get (self, IDnum):
        """
        returns a reference to the dictionary for the mouse with given IDtag. if the mouse tag is not found, makes a new dictionary
        if fresh mice can be added, else returns an empty dicitonary if fresh mice are to be ignored
        """
        return self.miceDict.get (str(IDnum), None)

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
                continue
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
                    # TODO check this
            else: # other two choices are for adding a mouse by RFID Tag, either reading from Tag Reader, or typing it
                self.add(event)
        response = input('Save changes in settings to a json file, too? (recommended). Make sure you ')
        if response[0] == 'Y' or response[0] == 'y':
            CAD.Dict_to_file(self.miceDict, "mice", self.jsonName, ".jsn")
    def hardwareTest(self):
        from time import sleep
        while True:
            inputStr = '\n change the following variables. \nEnter:\n'
            inputStr += '0 leave settings'
            inputStr += '1 inChamberTimeLimit'
            inputStr += '2 store Dictionary in Database'
            event = input(inputStr)
            if event == 0:
                break
            if event == '1':
                result = input('Enter in-Chamber duration limit, in minutes, before stopping head-fix trials, currently {:.2f}: '.format(self.inChamberTimeLimit / 60))
                if result != '':
                    self.settingsDict.update({'inChamberTimeLimit': int(result * 60)})
            if event == '2':
                result = input()
                #TODO
        self.setup()
from AHF_Task import Task

from AHF_Reader import AHF_Reader
from AHF_Base import AHF_Base
