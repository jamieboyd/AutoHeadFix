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
from AHF_TagReader import AHF_TagReader
import AHF_ClassAndDictUtils as CAD

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
    def __init__ (self, fileName = ''):
        """
        Initializes a Task object with hardware settings and experiment settings by calling loadSettings function
        
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
        ########## Head Fixer (optional) makes its own dictionary #################################
        if not hasattr (self, 'HeadFixerClass') or not hasattr (self, 'HeadFixerDict'):
            tempInput = input ('Does this setup have a head fixing mechanism installed? (Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.HeadFixerClass =  CAD.Class_from_file('HeadFixer', CAD.File_from_user ('HeadFixer', 'Head Fixer Class', '.py'))
                self.HeadFixerDict = self.HeadFixerClass.config_user_get ()
            else:
                self.HeadFixerClass = None
                self.HeadFixerDict = None
            fileErr = True
        ################################ Stimulator (Obligatory) makes its own dictionary #######################
        if not hasattr (self, 'StimulatorClass') or not hasattr (self, 'StimulatorDict'):
            self.StimulatorClass = CAD.Class_from_file('Stimulator', CAD.File_from_user ('Stimulator', 'Experiment Stimulator Class', '.py'))
            self.StimulatorDict = self.StimulatorClass.config_user_get ()
            fileErr = True
        ################################ Rewarder (Obligatory) class makes its own dictionary #######################
        if not hasattr (self, 'RewarderClass') or not hasattr (self, 'RewarderDict'):
            self.RewarderClass = CAD.Class_from_file('Rewarder', CAD.File_from_user ('Rewarder', 'Rewarder', '.py'))
            self.RewarderDict = self.RewarderClass.config_user_get ()
            fileErr = True
        ############################ TagReader (Obligatory) makes its own dictionary ##############
        if not hasattr (self, 'TagReaderClass') or not hasattr (self, 'TagReaderDict'):
            self.TagReaderClass = CAD.Class_from_file('TagReader', CAD.File_from_user ('TagReader', 'RFID-Tag Reader', '.py'))
            self.TagReaderDict = self.TagReaderClass.config_user_get ()
            fileErr = True
        ################################ Camera (optional) makes its own dictionary of settings ####################
        if not hasattr (self, 'cameraClass') or not hasattr (self, 'cameraDict'):
            tempInput = input ('Does this system have a main camera installed (Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.CameraClass = CAD.Class_from_file(CAD.File_from_user ('Camera', 'main camera', '.py'))
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
       
        ############################## LickDetector (optional) is not subclassable, so does not make its own dictionary ##############
        if not hasattr (self, 'lickDetectorIRQ'):
            tempInput = input ('Does this setup have a Lick Detector installed? (Y or N)')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.lickDetectorIRQ = int (input ('Enter the GPIO pin connected to the IRQ pin for the Lick Detector'))
            else:
                self.lickDetectorIRQ = 0
            fileErr = True
        ############################ A single GPIO pin for brain illumination ###########
        if not hasattr (self, 'LEDpin'):
            self.LEDpin = int (input ('Enter the GPIO pin connected to the blue LED for brain camera illumination:'))
            fileErr = True
            
         ####### settings for experiment configuration ########  
        if not hasattr (self, 'cageID'):
            self.cageID = input('Enter a name for the cage ID:')
            fileErr = True
        if not hasattr (self, 'dataPath'):
            self.dataPath = input ('Enter the path to the directory where the data will be saved:')
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
            self.propHeadFix = float (min (1, max (0, self.propHeadFix))) # make sure proportion is bewteen 0 and 1
            fileErr = True
        if not hasattr (self, 'skeddadleTime'):
            self.skeddadleTime = float (input ('Enter time, in seconds, for mouse to get head off the contacts when session ends:'))
            fileErr = True
        if not hasattr (self, 'inChamberTimeLimit'):
            self.inChamberTimeLimit = float(input('In-Chamber duration limit, seconds, before stopping head-fix trials:'))
        ############################ text messaging using textbelt service (Optional) not subclassable ######################
        if not hasattr (self, 'NotifierDict'):
            tempInput = input ('Send text messages if mouse exceeds criterion time in chamber?(Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.NotifierClass = CAD.Class_from_file('Notifier', '')
                self.NotifierDict = self.NotifierClass.config_user_get()
                self.NotifierDict.update ({'cageID' : self.cageID})
            else:
                self.NotifierClass = None
                self.NotifierDict = None
            fileErr = True
        ####################################### UDP triggers for alerting other computers (Optional) not subclassable ######################3
        if not hasattr (self, 'UDPTrigDict'):
            tempInput = input ('Send UDP triggers to start tasks on secondary computers (Y or N):')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.UDPTrigClass = CAD.Class_from_file('UDPTrig', '')
                self.UDPTrigDict = self.UDPTrigClass.config_user_get()
            else:
                self.UDPTrigDict = None
            fileErr = True
       
        # if some of the paramaters were set by user, give option to save
        if fileErr: 
            response = input ('Save new/updated settings to a task configuration file?')
            if response [0] == 'y' or response [0] == 'Y':
                self.saveSettings ()
                
                
    def saveSettings(self):
        """
        Saves current configuration stored in the task object into AHF_task_*.jsn
        Call this function after modifying the contents of the task to save your changes

        :param: none
        :returns: nothing
        """
        # get name for new config file and massage it a bit
        if self.fileName == '':
            promptStr = 'Enter a name to save task settings as file:'
        else:
            promptStr = 'Enter a name to save task settings, or enter to use current name, \'' + self.fileName + '\':'
        newConfig = input (promptStr)
        if self.fileName == '' and newConfig == '':
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
        print ('\n*************** Current Program Settings *******************')
        showDict = collections.OrderedDict()
        itemDict = {}
        nP = 0
        for key, value in sorted(self.__dict__.items()) :
        #for key, value in inspect.getmembers(self):
            if key.startswith ('_') is False and inspect.isroutine (getattr (self, key)) is False:
                showDict.update ({nP:{key: value}})
                nP += 1
        for ii in range (0, nP):
            itemDict.update (showDict [ii])
            kvp = itemDict.popitem()
            print(str (ii + 1) +') ', kvp [0], ' = ', kvp [1])
        print ('**********************************\n')
        return showDict
    

    def editSettings (self):
        itemDict = {}
        while True:
            showDict = self.showSettings()
            inputNum = int (input ('Enter number of setting to edit, or 0 to exit:'))
            if inputNum == 0:
                break
            else:
                itemDict.update (showDict [inputNum -1])
                kvp = itemDict.popitem()
                itemKey = kvp [0]
                itemValue = kvp [1]
                ### do special settings, subclassed things with extra user input needed #####
                ### these classes use same utility functions to get class names and settings dictionaries
                if itemKey.endswith ('Class'):
                    baseName = itemKey.rstrip ('Class')
                    newClassName = CAD.File_from_user (baseName, baseName, '.py')
                    newClass = CAD.Class_from_file (baseName, newClassName)
                    setattr (self, itemKey, newClass)
                    # new class needs  new dict
                    dictName = baseName + 'Dict'
                    newDict = newClass.config_user_get ()
                    setattr (self, dictName, newDict)
                elif itemKey.endswith ('Dict'):
                    baseName = itemKey.rstrip ('Dict')
                    theClass = getattr (self, baseName + 'Class')
                    if theClass is None:
                        newClassName = CAD.File_from_user (baseName, baseName, '.py')
                        newClass = CAD.Class_from_file (baseName, newClassName)
                        setattr (self, baseName + 'Class', newClass)
                    setattr (self, itemKey, newClass)
                    setattr (self, itemKey, newClass.config_user_get ())
                #####  other settings can be handled in a more generic way ##########################
                elif type (itemValue) is str:
                    inputStr = input ('Enter a new text value for %s, currently %s:' % (itemKey, str (itemValue)))
                    setattr (self, itemKey, inputStr)
                elif type (itemValue) is int:
                    inputStr = input ('Enter a new integer value for %s, currently %s:' % (itemKey, str (itemValue)))
                    setattr (self, itemKey, int (inputStr))
                elif type (itemValue) is float:
                    inputStr = input ('Enter a new floating point value for %s, currently %s:' % (itemKey, str (itemValue)))
                    setattr (self, itemKey, float (inputStr))
                elif type (itemValue) is tuple:
                    inputStr = input ('Enter a new comma separated list for %s, currently %s:' % (itemKey, str (itemValue)))
                    setattr (self, itemkey, tuple (inputStr.split(',')))
                elif type (itemVale) is bool:
                    inputStr = input ('%s, True for or False?, currently %s:' % (itemKey, str (itemValue)))
                    if inputStr [0] == 'T' or inputStr [0] == 't':
                        setattr (self, itemkey, True)
                    else:
                        setattr (self, itemkey, False)
                
                            

if __name__ == '__main__':
    task = Task ('')
    task.editSettings()


"""       
                
        try:
            with open ('AHFconfig.jsn', 'r') as fp:
                data = fp.read()
                data=data.replace('\n', ',')
                configDict = json.loads(data)
                fp.close()
                for key in configDict:
                    setattr (self, key, configDict.get(key))
                print (self.__dict__)
                if not hasattr (self, 'cageID'):
                    self.cageID = input('Enter the cage ID:')


                #print (inspect.getmembers (self))
                self.cageID = configDict.get('Cage ID')
                self.headFixerName = configDict.get('Head Fixer')
                AHF_HeadFixer.get_class (self.headFixerName).configDict_read (self, configDict)
                self.rewardPin = configDict.get('Reward Pin')
                self.tirPin = configDict.get('Tag In Range Pin')
                self.contactPin = configDict.get('Contact Pin')              
                self.contactPolarity = configDict.get('Contact Polarity') # RISING or FALLING, GPIO.RISING = 31, GPIO.FALLING = 32
                self.contactPUD = configDict.get('Contact Pull Up Down') # OFF, DOWN, or UP, GPIO.PUD_OFF=20, GPIO.PUD_DOWN =21, GPIO.PUD_UP=2
                self.ledPin = configDict.get('LED Pin') # OFF, DOWN, or UP, GPIO.PUD_OFF=20, GPIO.PUD_DOWN =21, GPIO.PUD_UP=22
                self.serialPort = configDict.get('Serial Port')
                self.hasLickDetector = configDict.get('has Lick Detetctor', False)
                if self.hasLickDetector:
                    self.lickIRQ = configDict.get('Lick IRQ Pin')
                    self.lickChans = configDict.get ('Lick Channels')
                self.dataPath = configDict.get('Path to Save Data')
                self.mouseConfigPath = configDict.get('Path to Mouse Config Data')
                self.hasEntryBeamBreak = configDict.get ('Has Entry Beam Break', False)
                if self.hasEntryBeamBreak:
                    self.entryBBpin = configDict.get('Entry Beam Break Pin')
        except (TypeError, IOError, ValueError) as e: #we will make a file if we didn't find it, or if it was incomplete
            print ('Unable to open base configuration file, AHFconfig.jsn, let\'s make new settings.\n')
            self.cageID = input('Enter the cage ID:')
            self.dataPath = configDict.get('Path to Save Data')
            self.mouseConfigPath = configDict.get('Path to Mouse Config Data')
            self.headFixerName = AHF_HeadFixer.get_HeadFixer_from_user()
            AHF_HeadFixer.get_class (self.headFixer).config_user_get (self)
            self.rewardPin = int (input ('Enter the GPIO pin connected to the water delivery solenoid:'))
            self.contactPin = int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:'))
            contactInt = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
            if contactInt == 0:
                self.contactPolarity = 'FALLING' # string for readbility, writing back to JSON
                self.contactEdge = GPIO.FALLING  # numeric constants defined in GPIO class
                self.noContactEdge = GPIO.RISING 
                self.contactState = GPIO.LOW
                self.noContactState = GPIO.HIGH
            else:
                self.contactPolarity = 'RISING'
                self.contactEdge = GPIO.RISING 
                expSettings.noContactEdge = GPIO.FALLING
                expSettings.contactState = GPIO.HIGH
                expSettings.noContactState = GPIO.LOW 
            contactInt = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
            if contactInt ==0:
                self.contactPUD = 'OFF'
            elif contactInt == 1:
                self.contactPUD = 'DOWN'
            else:
                self.contactPUD = 'UP'
            self.ledPin =  int (input ('Enter the GPIO pin connected to the blue LED for camera illumination:'))
            self.serialPort =  input ('Enter serial port for tag reader(likely either /dev/Serial0 or /dev/ttyUSB0):')
            self.tirPin =  int (input ('Enter the GPIO pin connected to the Tag-in-Range pin on the Tag reader:'))
            hasEntryBB = input('Does the experimental tube have a beam break at the entry, (yes or no):')
            if hasEntryBB [0] == 'Y' or hasEntryBB [0] == 'y':
                self.entryBBpin =  int (input ('Enter the GPIO pin connected to the beam break at the tube entrance:'))
            else:
                delattr (self, entryBBpin)
            self.showCageSet()
            doSave = input ('Enter \'e\' to re-edit the new Cage settings, or any other character to save the new settings to a file.')
            if doSave == 'e' or doSave == 'E':
                self.editCageSet()
            else:
                self.saveCageSet()
        # load experiment settings from file 
        hasFile = False
        if fileName is not None:
            if fileName.startswith ('AHFexp_'):
                configFile = ''
            else:
                configFile = 'AHFexp_'
            configFile += fileName
            if not fileName.endswith ('.jsn'):
                configFile += '.jsn'
            for f in os.listdir('.'):
                if f == configFile:
                    hasFile=True
                    break
        if hasFile:
            self.loadExpSettings (fileName)
        else:
        # look for experiment config files in the current directory, they start with AHFexp_ and end with .jsn
            iFile=0
            files = ''
            for f in os.listdir('.'):
                if f.startswith ('AFHexp_') and f.endswith ('.jsn'):
                    files += '\n' + str (iFile) + ':' + f
                    iFile +=1
            if iFile == 0: # no files found, create one
                print ('Unable to find an experiment config file, let\'s make a new configuration:')
                fileNum=-1
            else:
                inputPrompt = 'Enter file number to load experiment config file, or -1 to make new config\n'
                inputPrompt += files +'\n:'
                fileNum = int (input (inputPrompt))
            if fileNum == -1:
                self.expSettingsFromUser()
                self.saveExpSettings()
            else:
                # file list starts with a separator (\n) so we split the list on \n and get fileNum + 1
                # each list item starts with fileNum: so split the list item on ":" and get item 1 to get file name
                self.loadExpSettings ((files.split('\n')[fileNum + 1]).split (':')[1])
  


    def saveCageSet(self):
        
        #Saves current configuration stored in the task object into the file ./AHFconfig.jsn
        #Call this function after modifying the contents of the task to save your changes

        #:param: none
        #:returns: nothing
    
        jsonDict={'Cage ID':self.cageID,'Head Fixer':self.headFixer}
        AHF_HeadFixer.get_class (self.headFixer).configDict_set (self, jsonDict)
        jsonDict.update ({'Reward Pin':self.rewardPin, 'Tag In Range Pin':self.tirPin, 'Contact Pin':self.contactPin})
        jsonDict.update ({'Contact Polarity':self.contactPolarity, 'Contact Pull Up Down':self.contactPUD})
        jsonDict.update ({'LED Pin' : self.ledPin, 'Serial Port' : self.serialPort, 'Path to Save Data':self.dataPath, 'Mouse Config Path':self.mouseConfigPath})
        if hasattr(self, 'entryBBpin'):
            jsonDict.update ({'Entry Beam Break Pin':self.entryBBpin})
        with open ('AHFconfig.jsn', 'w') as fp:
            fp.write (json.dumps (jsonDict), sort_keys = True, separators=('\n', ':'))
            fp.close ()
            uid = pwd.getpwnam ('pi').pw_uid
            gid = grp.getgrnam ('pi').gr_gid
            os.chown ('AHFconfig.jsn', uid, gid) # we may run as root for pi PWM, so we need to expicitly set ownership

    def showCageSet (self):
        
        #Prints the current configuration stored in this AHF_CageSet to the console, nicely formatted

        #:param: none
        #:returns: nothing
        
        print ('****************Current Auto-Head-Fix Cage Settings********************************')
        print ('1:Cage ID=' + str (self.cageID))
        print ('2:data Path=' + self.dataPath)
        print ('3:mouse Config path=' + self.mouseConfigPath)
        print ('4:Head Fix method=' + self.headFixer)
        print ('5:' + AHF_HeadFixer.get_class (self.headFixer).config_show(self))
        print ('6:Reward Solenoid Pin=' + str (self.rewardPin))
        print ('7:Tag-In-Range Pin=' + str (self.tirPin))
        print ('8:Contact Pin=' + str(self.contactPin))
        print ('9:Contact Polarity =' + str(self.contactPolarity) + ' and contact Pull Up Down = ' + str(self.contactPUD))
        print ('10:Brain LED Illumination Pin=' + str(self.ledPin))
        print ('11:Tag Reader serialPort=' + self.serialPort)
        if hasattr(self, 'entryBBpin'):
            print ('12:Has Entry Beam Break = True, Pin=' + str (self.entryBBpin))
        else:
            print ('12:Has Entry Beam Break = False')
        print ('**************************************************************************************')


    def editCageSet (self):
        
        #Allows the user to edit and save the cage settings
        
        while True:
            self.showCageSet ()
            editNum = int(input ('Enter number of paramater to Edit, or 0 when done to save file:'))
            if editNum == 0:
                break
            elif editNum == 1:
                self.cageID = input('Enter the cage ID:')
            elif editNum == 2:
                self.dataPath = input ('Enter the path to the directory where the data will be saved:')
            elif editNum == 3:
                self.dataPath = input ('Enter the path to the directory from which mouse configuration data can be loaded:')
            elif editNum == 4:
                self.headFixerName = AHF_HeadFixer.get_HeadFixer_from_user()
            elif editNum == 5:
                AHF_HeadFixer.get_class (self.headFixerName).config_user_get (self)
            elif editNum == 6:
                self.rewardPin = int (input ('Enter the GPIO pin connected to the water delivery solenoid:'))
            elif editNum == 7:
                task.tirPin= int (input ('Enter the GPIO pin connected to the Tag-in-Range pin on the Tag reader:'))
            elif editNum == 8:
                task.contactPin= int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:'))
            elif editNum == 9:
                contactInt = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
                if contactInt == 0:
                    self.contactPolarity = 'FALLING'
                else:
                    self.contactPolarity = 'RISING'
                contactInt = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
                if contactInt ==0:
                    self.contactPUD = 'OFF'
                elif contactInt == 1:
                    self.contactPUD = 'DOWN'
                else:
                    self.contactPUD='UP'
            elif editNum == 10:
                self.ledPin = int (input ('Enter the GPIO pin connected to the blue LED for camera illumination:'))
            elif editNum == 11:
                task.serialPort = input ('Enter serial port for tag reader(likely either /dev/ttyAMA0 or /dev/ttyUSB0):')
            elif editNum == 12:
                inputInt =  int (input('GPIO pin for the beam break at the entry of the experimental tube, or -1 for no entery bean break:'))
                if inputInt == -1:
                    delattr (self, 'entryBBpin')
                else:
                    self.entryBBpin = inputInt
            else:
                print ('I don\'t recognize that number ' + str (editNum))
        self.saveCageSet()

    def loadExpSettings (self, fileName):
        with open (fileName, 'r') as fp:
            data = fp.read()
            data=data.replace('\n', ',')
            configDict = json.loads(data);print (configDict)
            fp.close()
            self.fileName = fileName
            self.entranceRewardTime = float (configDict.get ('entranceRewardTime', 30e-03))
            self.taskRewardTime = float (configDict.get ('taskRewardTime', 30e-03))
            self.maxEntryRewards = int (configDict.get ('maxEntryRewards', 100))
            self.entryRewardDelay = float (configDict.get('entryRewardDelay', 0.5))
            self.propHeadFix = float (configDict.get('propHeadFix', 1.0))
            self.skeddadleTime = float (configDict.get ('skeddadleTime', 0.25))
            self.inChamberTimeLimit = float (configDict.get ('inChamberTimeLimit',600))
            self.hasTextMsg = bool (configDict.get ('hasTextMsg', False))
            if self.hasTextMsg == True:
                self.phoneList = tuple (configDict.get('phoneList'))
            self.hasUDP = bool(configDict.get ('hasUDP', False))
            if self.hasUDP == True:
                self.UDPList = tuple (configDict.get ('UDPList'))
                self.cameraStartDelay = float (configDict.get('cameraStartDelay'))
            self.camParamsDict = configDict.get('camParams', {})
            self.stimulator = configDict.get('stimulator')
            self.stimDict = configDict.get('stimParams')
"""

