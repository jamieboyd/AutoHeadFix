#! /usr/bin/python
#-*-coding: utf-8 -*-


"""
We copy all variables from cage settings and exp settings, plus references to all created objects,
into a single object called Task

"""
import inspect
import collections
from collections import OrderedDict
import json
import os
import pwd
import grp
import AHF_ClassAndDictUtils as CAD
from abc import ABCMeta
from AHF_Base import AHF_Base
import RPi.GPIO as GPIO

gTask = None

class Task(object):
    """
    The plan is to copy all variables from settings, user, into a single object
    The object will have fields for things loaded from hardware config dictionary and experiment config dictionary
    as well as fields for objects created when program runs (headFixer, TagReader, rewarder, camera, stimulator)
    Objects that are created will have a dictionary of their own as an entry in the main dictionay
    Using the same names in the object fields as in the dictionary, and only loading one dictionary from
    a combined settings file, we don't need a dictionary while thr program is running because the task object can recreate the dict
    with self.__dict__
    """
    def __init__ (self, fileName = ''):
        """
        Initializes a Task object with settings for various hardware, stimulator, and Subjects classes

        """
        fileErr = False
        if fileName != '':
            # file name passed in may or may not start with AFH_task_ and end with .jsn
            self.fileName = fileName
            if self.fileName.startswith ('AHF_task_'):
                self.fileName = self.filename[9:]
            if self.fileName.endswith ('.jsn'):
                self.filename = self.fileName.rstrip ('.jsn')
            if not CAD.File_exists ('task', self.fileName, '.jsn'):
                self.fileName = ''
        else:
            self.fileName = ''
        # no file passed in, or passed in file could not be found. Get user to choose a file
        if self.fileName == '':
            try:
                self.fileName = CAD.File_from_user ('task', 'Auto Head Fix task configuration', '.jsn', True)
            except FileNotFoundError:
                self.fileName = ''
                print ('Let\'s configure a new task.\n')
                fileErr = True
        # if we found a file, try to load it
        if self.fileName != '':
            try:
                CAD.File_to_obj_fields ('task', self.fileName, '.jsn', self)
            except ValueError as e:
                print ('Unable to open and fully load task configuration:' + str (e))
                fileErr = True
        # check for any missing settings, all settings will be missing if making a new config, and call setting functions for
        # things like head fixer that are subclassable need some extra work , when either loaded from file or user queried
        ########## Head Fixer (obligatory) makes its own dictionary #################################
        if not hasattr (self, 'HeadFixerClass') or not hasattr (self, 'HeadFixerDict'):
            self.HeadFixerClass =  CAD.Class_from_file('HeadFixer', CAD.File_from_user ('HeadFixer', 'Head Fixer Class', '.py'))
            self.HeadFixerDict = self.HeadFixerClass.config_user_get ()
            fileErr = True
        ################################ Stimulator (Obligatory) makes its own dictionary #######################
        if not hasattr (self, 'StimulusClass') or not hasattr (self, 'StimulusDict'):
            self.StimulusClass = CAD.Class_from_file('Stimulus', CAD.File_from_user ('Stimulus', 'Experiment Stimulus Class', '.py'))
            #requires a starter dict?
            self.StimulusDict = self.StimulusClass.config_user_get ()
            fileErr = True
        ################################ Stimulator (Obligatory) makes its own dictionary #######################
        if not hasattr (self, 'StimulatorClass') or not hasattr (self, 'StimulatorDict'):
            self.StimulatorClass = CAD.Class_from_file('Stimulator', CAD.File_from_user ('Stimulator', 'Experiment Stimulator Class', '.py'))
            #requires a starter dict?
            self.StimulatorDict = self.StimulatorClass.config_user_get ()
            fileErr = True
        ################################ Rewarder (Obligatory) class makes its own dictionary #######################
        if not hasattr (self, 'RewarderClass') or not hasattr (self, 'RewarderDict'):
            self.RewarderClass = CAD.Class_from_file('Rewarder', CAD.File_from_user ('Rewarder', 'Rewarder', '.py'))
            self.RewarderDict = self.RewarderClass.config_user_get ()
            fileErr = True
        ############################ Reader (Obligatory) makes its own dictionary ##############
        if not hasattr (self, 'ReaderClass') or not hasattr (self, 'ReaderDict'):
            self.ReaderClass = CAD.Class_from_file('Reader', CAD.File_from_user ('Reader', 'RFID-Tag Reader', '.py'))
            self.ReaderDict = self.ReaderClass.config_user_get ()
            fileErr = True
        ################################ Camera (optional) makes its own dictionary of settings ####################
        if not hasattr (self, 'CameraClass') or not hasattr (self, 'CameraDict'):
            tempInput = input ('Does this system have a main camera installed (Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.CameraClass = CAD.Class_from_file('Camera', CAD.File_from_user ('Camera', 'main camera', '.py'))
                self.CameraDict = self.CameraClass.config_user_get ()
            else:
                self.cameraClass = None
                self.cameraDict = None
            fileErr = True
        ############################# ContactCheck (Obligatory) makes its own dictionary of settings ###################
        if not hasattr (self, 'ContactCheckClass') or not hasattr (self, 'ContactCheckDict'):
            self.ContactCheckClass = CAD.Class_from_file('ContactCheck', CAD.File_from_user ('ContactCheck', 'Contact Checker', '.py'))
            self.ContactCheckDict = self.ContactCheckClass.config_user_get ()
            fileErr = True
        ############################ NOT just A single GPIO pin for brain illumination, unless you want that ###########
        if not hasattr (self, 'BrainLightClass') or not hasattr (self, 'BrainLightDict'):
            self.BrainLightClass = CAD.Class_from_file('BrainLight', CAD.File_from_user ('BrainLight', 'Brain illuminator', '.py'))
            self.BrainLightDict = self.BrainLightClass.config_user_get ()
            fileErr = True
        ####################################### triggers for alerting other computers (Optional) only 1 subclass so far ######################3
        if not hasattr (self, 'TriggerClass') or not hasattr (self, 'TriggerDict'):
            tempInput = input ('Send triggers to start tasks on secondary computers (Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.TriggerClass = CAD.Class_from_file('Trigger', CAD.File_from_user ('Trigger', 'Trigger', '.py'))
                self.TriggerDict = self.TriggerClass.config_user_get()
            else:
                self.TriggerClass = None
                self.TriggerDict = None
            fileErr = True
        ############################## LickDetector (optional) only 1 subclass so far ##############
        if not hasattr (self, 'LickDetectorClass') or not hasattr (self, 'LickDetectorDict'):
            tempInput = input ('Does this setup have a Lick Detector installed? (Y or N)')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.LickDetectorClass = CAD.Class_from_file('LickDetector', CAD.File_from_user ('LickDetector', 'Lick Detector', '.py'))
                self.LickDetectorDict = self.LickDetectorClass.config_user_get()
            else:
                self.LickDetectorClass = None
                self.LickDetectorDict = None
            fileErr = True
        ###################### DataLogger (Obligatory) for logging data in text files, or database of HD5,or .... #################
        if not hasattr(self, 'DataLoggerClass') or not hasattr(self, 'DataLoggerDict'):
            self.DataLoggerClass = CAD.Class_from_file('DataLogger', CAD.File_from_user('DataLogger', 'Data Logger', '.py'))
            self.DataLoggerDict = self.DataLoggerClass.config_user_get()
            fileErr = True
        ############################ text messaging using textbelt service (Optional) only 1 subclass so far ######################
        if not hasattr(self, 'NotifierClass') or not hasattr(self, 'NotifierDict'):
            tempInput = input('Send notifications if subject exceeds criterion time in chamber?(Y or N):')
            if tempInput[0] == 'y' or tempInput[0] == 'Y':
                self.NotifierClass = CAD.Class_from_file('Notifier', CAD.File_from_user('Notifier', 'Text Messaging Notifier','.py'))
                self.NotifierDict = self.NotifierClass.config_user_get()
                self.NotifierDict.update({'cageID': self.DataLoggerDict.get('cageID')})
            else:
                self.NotifierClass = None
                self.NotifierDict = None
            fileErr = True
        ############################## Subjects only 1 subclass so far (generic mice) ##############
        if not hasattr(self, 'SubjectsClass') or not hasattr(self, 'SubjectsDict'):
            self.SubjectsClass = CAD.Class_from_file('Subjects',CAD.File_from_user('Subjects', 'test subjects', '.py'))
            self.SubjectsDict = self.SubjectsClass.config_user_get()
            fileErr = True
        ###################### things we track in the main program #################################
        self.tag = 0    # RFIG tag number, 0 for no tag, updated by threaded callback
        self.contact = False # true if contact is true
        self.contactTime = 0
        self.lastFixedTag = 0
        self.lastFixedTime = 0
        self.entryTime = 0.0
        self.fixAgainTime = float ('inf')
        self.inChamberLimitExceeded = False
        self.edited = False
        self.logToFile = True # a flag for writing to the shell only, or to the shall and the log
        ################ if some of the paramaters were set by user, give option to save ###############
        if fileErr:
            response = input ('Save new/updated settings to a task configuration file?')
            if response [0] == 'y' or response [0] == 'Y':
                self.saveSettings ()



    def setup (self):
        """
        Sets up hardware and other objects that need setting up, each object is made by initing a class with a dictionary
        """
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        fields = sorted(inspect.getmembers (self))
        for item in fields:
            if isinstance(item [1],  ABCMeta):
                baseName = (item [0], item[0][:-5])[item[0].endswith('Class')]
                classDict = getattr (self, baseName + 'Dict')
                setattr (self, baseName, item [1](self, classDict))
        global gTask
        gTask = self
        default = False
        if self.edited:
            temp = input("Do you want to make these your default settings? (y/n)")
            if str(temp[0]).lower() == "y":
                default = True
            for item in fields:
                if isinstance(item [1],  ABCMeta):
                    baseName = (item [0], item[0][:-5])[item[0].endswith('Class')]
                    classDict = getattr (self, baseName + 'Dict')
                    self.DataLogger.storeConfig("changed_hardware", classDict, baseName)
                    if default:
                        self.DataLogger.storeConfig("default_hardware", classDict, baseName)

    def saveSettings(self):
        """
        Saves current configuration stored in the task object into AHF_task_*.jsn
        Call this function after modifying the contents of the task to save your changes

        :param: none
        :returns: nothing
        """
        self.edited = True
        # get name for new config file and massage it a bit
        if self.fileName == '':
            promptStr = 'Enter a name to save task settings as file:'
        else:
            promptStr = 'Enter a name to save task settings, or enter to use current name, \'' + self.fileName + '\':'
        newConfig = input (promptStr)
        if self.fileName != '' and newConfig == '':
            newConfig = self.fileName
        else:
            if newConfig.startswith ('AHF_task_'):
                newConfig = newConfig [9 :]
            if newConfig.endswith ('.jsn'):
                newConfig.rstrip('.jsn')
            newConfig = ''.join([c for c in newConfig if c.isalpha() or c.isdigit() or c=='_'])
            self.fileName = newConfig
        CAD.Obj_fields_to_file (self, 'task', newConfig, '.jsn')

    def showSettings (self):
        """
        Prints settings to screen in a numbered fashion from an ordered dictionary, making it easy to select a setting to
        change. Returns the ordered dictionary, used by editSettings function
        """
        return CAD.Show_ordered_object (self, 'Auto Head Fix Task')


    def editSettings (self):
        if (CAD.Edit_Obj_fields (self,  'Auto Head Fix Task')):
            response = input ('Save changes in settings to a file?')
            if response [0] == 'Y' or response [0] == 'y':
                self.saveSettings ()


    def Show_testable_objects (self):
        print ('\n*************** Testable Auto Head Fix Objects *******************')
        showDict = OrderedDict()
        itemDict = {}
        nP = 0
        fields = sorted (inspect.getmembers (self))
        for item in fields:
           if isinstance(item[1], AHF_Base) and hasattr (item[1], 'hardwareTest'):
                showDict.update ({nP:{item [0]: item [1]}})
                nP +=1
        # print to screen
        for ii in range (0, nP):
            itemDict.update (showDict.get (ii))
            kvp = itemDict.popitem()
            print(str (ii + 1) +') ', kvp [0], ' = ', kvp [1])
        print ('**********************************\n')
        return showDict


    def hardwareTester (self):
        while True:
            showDict = self.Show_testable_objects ()
            inputStr = input ('Enter number of object to test, or 0 to exit:')
            try:
                inputNum = int (inputStr)
            except ValueError as e:
                print ('enter a NUMBER for testing, please: %s\n' % str(e))
                continue
            if inputNum == 0:
                break
            else:
                itemDict = {}
                itemDict.update (showDict [inputNum -1]) #itemDict = OrderedDict.get (inputNum -1)
                kvp = itemDict.popitem()
                itemValue = kvp [1]
                itemValue.hardwareTest ()
        response = input ('Save changes in settings to a file?')
        if response [0] == 'Y' or response [0] == 'y':
            self.saveSettings ()


if __name__ == '__main__':
    task = Task ('')
    task.editSettings()
    response = input ('Save settings to file?')
    if response [0] == 'Y' or response [0] == 'y':
        task.saveSettings ()
    task.setup ()
    task.hardwareTester ()
