#! /usr/bin/python
#-*-coding: utf-8 -*-


"""
We copy all variables from cage settings and exp settings, plus references to all created objects,
into a single object called Task

"""
import inspect
import collections
import json
import os
import pwd
import grp
from AHF_HeadFixer import AHF_HeadFixer
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Camera import AHF_Camera
from AHF_ClassAndDictUtils import AHF_class_from_file, AHF_file_exists, AHF_file_from_user, AHF_show_ordered_dict
from AHF_ClassAndDictUtils import AHF_edit_dict, AHF_obj_fields_to_file, AHF_file_to_obj_fields

class Task:
    """
    The plan is to copy all variables from settings, user, into a single object
    The object will have fields for things loaded from hardware config dictionary and experiment config dictionary
    as well as fields for objects created when program runs (headFixer, TagReader, rewarder, camera, stimulator)
    Objects that are created from subclassable objects will have a dictionary of their own as an entry in the main dictionay
    Using the same names in the object fields as in the dictionary, and only loading one dictionary from
    a combined settings file, we don't need a dictionary while thr program is running because the task object can recreate the dict
    with self.__dict__
    """
    def __init__ (self, fileName):
        """
        Initializes a Task object with hardware settings and experiment settings by calling loadSettings function
        
        """
        self.fileName = '' # where we save the name of the file settings were loaded from
        # load experiment settings from passed in file name, if program was started with a task file name 
        if fileName is not None:
            # file name passed in may or may not start with AFH_task_ and end with .jsn
            nameStr = filename.lstrip ('AHF_task_').rstrip ('.jsn')
            if AHF_file_exists ('task', nameStr, '.jsn'):
                self.fileName = 'AHF_task_' +  nameStr + '.jsn'
            else:
                self.fileName = ''
        # if we don't have a valid file name, get user to select one
        if self.fileName == '':
            try:
                self.fileName = AHF_file_from_user (nameStr, 'AHF task config file', '.jsn')
            except FileNotFoundError:
                self.fileName = ''
        # if we have a valid file name, load it
        if self.fileName != '':
            self.fileName =  self.filename.lstrip ('AHF_task_').rstrip ('.jsn')
            missingSettings = AHF_file_to_obj_fields ('task', self.fileName, 'AHF task configuration', '.jsn', self)
            if missingSettings:
                print ('Not all settings were loaded from %s file, let\'s fix the missing ones.' % self.fileName)
                self.checkSettings()    
        # if we don't have a valid file name, make configuration from scratch
        else:
            print ('No valid settings file, let\'s create new settings.')
            self.checkSettings()
            

    def checkSettings (self):
        """
        user is querried for amy or all missing settings. This is the only place in the code where all settings are described
        """
        # check for any missing settings, all settings will be missing if making a new config, and call setting functions for
        # things like head fixer that are subclassable need some extra work , when either loaded from file or user queried
        ########## Head Fixer (optoinal) makes its own dictionary #################################
        fileErr = False
        if not hasattr (self, 'hasHeadFixer') or not hasattr (self, 'headFixerClass') or not hasattr (self, 'headFixerDict'):
            tempInput = input ('Does this setup have a head fixing mechanism installed? (Y or N)')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasHeadFixer = True
                self.headFixerClass = AHF_HeadFixer.get_HeadFixer_from_user ()
                self.headFixerDict = AHF_HeadFixer.get_class(self.headFixerClass).config_user_get ()
            else:
                self.hasHeadFixer = False
                self.headFixerClass = None
                self.headFixerDict = {}
            fileErr = True
        ################################ Stimulator makes its own dictionary #######################
        if not hasattr (self, 'StimulatorClass') or not hasattr (self, 'StimulatorDict'):
            self.StimulatorClass = AHF_Stimulator.get_Stimulator_from_user ()
            self.StimulatorDict = AHF_Stimulator.get_class(self.StimulatorClass).config_user_get ()
            fileErr = True
        ################################ Rewarder class makes its own dictionary #######################
        if not hasattr (self, 'RewarderClass') or not hasattr (self, 'RewarderDict'):
            self.RewarderClass = AHF_Rewarder.get_Rewarder_from_user ()
            self.RewarderDict = AHF_Rewarder.get_class(self.RewarderClass).config_user_get ()
            fileErr = True
        ################################ Camera (optional) makes its own dictionary of settings ####################
        if not hasattr (self, 'hasCamera') or not hasattr (self, 'cameraClass') or not hasattr (self, 'cameraDict'):
            tempInput = input ('Does this system have a main camera installed (Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasCamera = True
                self.cameraClass = AHF_Camera.get_Camera_from_user ()
                self.cameraDict = AHF_Camera.get_class(self.CameraClass).config_user_get ()
            else:
                self.hasCamera=False
                self.cameraClass = None
                self.cameraDict = {}
            fileErr = True
        ############################# ContactCheck makes its own dictionary of settings ###################
        if not hasattr (self, 'ContactCheckClass') or not hasattr (self, 'ContactCheckDict'):
            self.ContactCheckClass = AHF_ContactCheck.get_ContactCheck_from_user ()
            self.ContactCheckDict = AHF_ContactCheck.get_class(self.ContactCheckClass).config_user_get ()
            fileErr = True
        ############################ TagReader is not subclassable, so does not make its own dictionary ##############
        if not hasattr (self, 'serialPort'):
            self.serialPort = input ('Enter serial port for tag reader(likely either /dev/Serial0 or /dev/ttyUSB0):')
            fileErr = True
        if not hasattr (self, 'TIRpin'):
            self.TIRpin = int (input('Enter the GPIO pin connected to the Tag-In-Range pin on the Tag Reader:'))
            fileErr = True
        ############################## LickDetector (optional) is not subclassable, so does not make its own dictionary ##############
        if not hasattr (self, 'hasLickDetector') or not hasattr (self, 'lickDetectorIRQ'):
            tempInput = input ('Does this setup have a Lick Detector installed? (Y or N)')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasLickDetector = True
                self.lickDetectorIRQ = int (input ('Enter the GPIO pin connected to the IRQ pin for the Lick Detector'))
            else:
                self.hasLickDetector = False
                self.lickDetectorIRQ = 0
            fileErr = True
        ############################ Remaining hardware things are single GPIO pins that are not defined in classes ###########
        if not hasattr (self, 'LEDpin'):
            self.LEDpin = int (input ('Enter the GPIO pin connected to the blue LED for camera illumination:'))
            fileErr = True
        """
        #### The entry beam break is not implemented in current systems, so is commented out for now
        if not hasattr(self, 'hasEntryBB') or not hasattr (self, 'entryBBpin'):
            tempInput = input ('Does this setup have a beam break installed at the tube enty way? (Y or N)')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasEntryBB = True
                self.entryBBpin = int (input ('Enter the GPIO pin connected to the entry beam break'))
            else:
                self.hasEntryBB = False
                self.entryBBpin = 0
            fileErr = True
        """
         ####### settings for experiment configuration ########  
        if not hasattr (self, 'cageID'):
            self.cageID = input('Enter a name for the cage ID:')
            fileErr = True
        if not hasattr (self, 'dataPath'):
            self.dataPth = input ('Enter the path to the directory where the data will be saved:')
            fileErr = True
        if not hasattr (self, 'mouseConfigPath'):
            self.mouseConfigPath = input ('Enter the path to the directory where mouse configuration data can be loaded:')
            #### the reward and head-fix proportion settings can also be set on a per-mouse bassis
            ### these provide default values
        if not hasattr (self, 'maxEntryRewards'):
            self.maxEntryRewards = int (input ('Enter maximum number of entry rewards that will be given per day:'))
            fileErr = True
        if not hasattr (self, 'entryRewardDelay'):
            self.entryRewardDelay= float (input('Enter delay, in seconds, before an entrance reward is given:'))
            fileErr = True
        if not hasattr (self, 'propHeadFix'):
            self.propHeadFix= float (input('Enter proportion (0 to 1) of trials that are head-fixed:'))
            self.propHeadFix = min (1, max (0, self.propHeadFix)) # make sure proportion is bewteen 0 and 1
            fileErr = True
        if not hasattr (self, 'skeddadleTime'):
            self.skeddadleTime = float (input ('Enter time, in seconds, for mouse to get head off the contacts when session ends:'))
            fileErr = True
        if not hasattr (self, 'inChamberTimeLimit'):
            self.inChamberTimeLimit = float(input('In-Chamber duration limit, seconds, before stopping head-fix trials:'))
        ############################ text messaging using textbelt service (Optional) not sunbclassable ######################
        if not hasattr (self, 'hasTextMsg') or not hasattr (self, 'phoneList') or not hasattr (self, 'textBeltKey'):
            tempInput = input ('Send text messages if mouse exceeds criterion time in chamber?(Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasTextMsg = True
                self.phoneList =tuple (input('Phone numbers to receive a text message if mouse is in chamber too long:').split(','))
                self.textBeltKey = input ('Enter the textBelt code (c\'mon it\'s only 65 characters):')
            else:
                self.hasTextMsg = False
                self.phoneList = ()
                self.textBeltKey = ''
            fileErr = True
        ####################################### UDP triggers for alerting other computers (Optional) not subclassable ######################3
        if not hasattr(self, 'hasUDP') or not hasattr (self, 'UDPList') or not hasattr (self,'UDPstartDelay') :
            tempInput = input ('Send UDP triggers to start tasks on secondary computers (Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasUDP = True
                self.UDPList =tuple (input('IP addresses of Pis running secondary cameras:').split (','))
                self.UDPstartDelay = float (input ('Delay in seconds between sending UDP and toggling blue LED.'))
            else:
                self.hasUDP = False
                self.UDPList = ()
                self.UDPstartDelay = 0
            fileErr = True
       
        # if some of the paramaters were set by user, give option to save
        if fileErr:
            self.saveSettings(True)



    def saveSettings (self, queryUser):
        if not queryUser:
            AHF_obj_fields_to_file (self, 'task', self.fileName, '.jsn')
        else:
            self.showSettings()
            response = input ('Save new/updated settings to a task configuration file?')
            if response [0] == 'y' or response [0] == 'Y':
                if self.fileName != '':
                    inputStr = 'Enter a name to save task settings, or enter to use current name, \'%s\':' % self.fileName
                    newConfig = input (inputStr)
                    if response == '':
                        newConfig = self.fileName
                else:
                    inputStr = 'Enter a name to save task settings:'
                    newConfig = input (inputStr)
                    newConfig = lstrip('AHF_task_').rstrip ('.jsn')
                AHF_obj_fields_to_file (self, 'task', newConfig, '.jsn')
                
                


    def showSettings (self):
        """
        Prints settings to screen in a numbered fashion from an ordered dictionary, making it easy to select a setting to
        change. Returns the ordered dictionary, used by editSettings function
        """
        return AHF_show_ordered_dict (self.__dict__, 'AHF Task Settings')
    


    def editSettings (self):
        while True:
            orderedDict = self.showSettings()
            updatDict = {}
            inputStr = input ('Enter number of setting to edit, or -1 to exit:')
            try:
                inputNum = int (inputStr)
            except ValueError as e:
                print ('enter a NUMBER for setting, please: %s\n' % str(e))
                continue
            if inputNum < 0:
                break
            else:
                itemDict = orderedDict.get (inputNum)
                kvp = itemDict.popitem()
                itemKey = kvp [0]
                itemValue = kvp [1]
                ### do special settings, subclassed things with extra user input needed #####
                ### these classes use same patterns of static functions to get class names and settings dictionaries
                if itemKey == 'RewarderClass':
                    self.RewarderClass = AHF_file_from_user ('Rewarder', 'AHF Rewarder class files', '.py')
                elif itemKey == 'RewarderDict':
                    self.RewarderDict = AHF_Rewarder.get_class(self.RewarderClass).config_user_get()
                elif itemkey == 'headFixerClass':
                    self.headFixerClass = AHF_HeadFixer.get_HeadFixer_from_user ()
                elif itemKey == 'headFixerDict':
                    self.headFixerDict = AHF_HeadFixer.get_class(self.headFixerClass).config_user_get ()
                elif itemKey == 'StimulatorClass': 
                    self.StimulatorClass = AHF_Stimulator.get_Stimulator_from_user ()
                elif itemKey == 'StimulatorDict':
                    self.StimulatorDict = AHF_Stimulator.get_class(self.StimulatorClass).config_user_get ()
                #####  other settings can be handled in a more generic way ##########################
                if type (itemValue) is str:
                    inputStr = input ('Enter a new text value for %s, currently %s:' % (itemKey, str (itemValue)))
                    setattr (self, itemKey, str (inputStr))
                elif type (itemValue) is int:
                    inputStr = input ('Enter a new integer value for %s, currently %s:' % (itemKey, str (itemValue)))
                    setattr (self, itemKey, int (inputStr))
                elif type (itemValue) is float:
                    inputStr = input ('Enter a new floating point value for %s, currently %s:' % (itemKey, str (itemValue)))
                    setattr (self, itemKey, float (inputStr))
                elif type (itemValue) is tuple or itemValue is list:
                    outputList = []
                    if type (itemValue [0]) is str:
                        inputStr = input ('Enter a new comma separated list of strings for %s, currently %s:' % (itemKey, str (itemValue)))
                        outputList = list (inputStr.split(','))
                    elif type (itemValue [0]) is int:
                        inputStr = input ('Enter a new comma separated list of integer values for %s, currently %s:' % (itemKey, str (itemValue)))
                        for string in inputStr.split(','):
                            try:
                                outputList.append (int (string))
                            except ValueError:
                                continue
                    elif type (itemValue [0]) is float:
                        inputStr = input ('Enter a new comma separated list of floating point values for %s, currently %s:' % (itemKey, str (itemValue)))
                        for string in inputStr.split(','):
                            try:
                                outputList.append (float (string))
                            except ValueError:
                                continue
                    if type (itemValue) is tuple:
                        setattr (self, itemKey,  tuple (outputList))
                    else:
                        setattr (self, itemKey,  outputList)
                elif type (itemValue) is bool:
                    inputStr = input ('%s, True for or False?, currently %s:' % (itemKey, str (itemValue)))
                    if inputStr [0] == 'T' or inputStr [0] == 't':
                        setattr (self, itemKey,  True)
                    else:
                        setattr (self, itemKey,  False)
                elif type (itemValue) is dict:
                    AHF_edit_dict (itemValue, itemKey)
                
        self.saveSettings (True)
                            



if __name__ == '__main__':
    task = Task (None)
    task.editSettings()
