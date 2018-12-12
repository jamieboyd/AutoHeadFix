#! /usr/bin/python
#-*-coding: utf-8 -*-


"""
We copy all variables from cage settings and exp settings, plus pointers to all created objects,
into a single object called Task

"""
import inspect
import json
import os
import pwd
import grp
from AHF_HeadFixer import AHF_HeadFixer
from AHF_Stimulator import AHF_Stimulator
from AHF_Camera import AHF_Camera

class Task:
    """
    The plan is to copy all variables from settings, user, into a single object
    The object will have fields for things loaded from hardware config dictionary and experiment config dictionary
    as well as fields for objects created when program runs (headFixer, TagReader, rewarder, camera, stimulator)
    Objects that are created from subclassable objects will have a dictionary of their own as an entry in the main dictionay
    Using the same names in the object fields as in the dictionary, and only loading one dictionary from
    a combined settings file, we don't need the dictionary because the task object can recreate the dict
    with self.__dict__
    """
    def __init__ (self, fileName):
        """
        Initializes a Task object with hardware settings and experiment settings by calling loadSettings function
        
        """
        # try to load ssettings from ./AHFtask_*.jsn, load it or query user if it does not exist or is incomplete
        fileLoaded = False
        self.fileName = ''
        # load experiment settings from passed in file name, if program was started with a task file name 
        if fileName is not None:
            # file name passed in may or may not start with AFHtask_ and end with .jsn
            if fileName.startswith ('AHFtask_'):
                configFile = ''
            else:
                configFile = 'AHFtask_'
            configFile += fileName
            if not fileName.endswith ('.jsn'):
                configFile += '.jsn'
            # try to find the file name in current directory and load it
            for f in os.listdir('.'):
                if f == configFile:
                    fileLoaded=self.loadSettings (configFile)
                    break
        if not fileLoaded:
            # look for all experiment config files in the current directory, they start with AHFtask_ and end with .jsn
            iFile=0
            files = ''
            for f in os.listdir('.'):
                if f.startswith ('AFHtask_') and f.endswith ('.jsn'):
                    files += '\n' + str (iFile) + ':' + f
                    iFile +=1
            if iFile == 0: # no files found, so set flag for user to create one
                print ('Unable to find any Auto head Fix task files, let\'s configure a new task:')
                fileNum=-1
            else:  # list all settings files and get user to choose one, or choose -1 to make new file anyway
                inputPrompt = 'Enter file number to load Auto Head Fix task file, or -1 to configure q new task\n'
                inputPrompt += files +'\n:'
                fileNum = int (input (inputPrompt))
            if fileNum == -1: # no settings file found, or user decided to make a new one, call loadSettings with None
                fileLoaded = self.loadSettings (None)
            else: # load user's chosen settings file. 
                # file list starts with a separator (\n) so we split the list on \n and get fileNum + 1
                # each list item starts with fileNum: so split the list item on ":" and get item 1 to get file name
                fileLoaded = self.loadSettings ((files.split('\n')[fileNum + 1]).split (':')[1])
        

    def loadSettings (self, fileName):
        """
        Loads settings from a JSON text file in current folder, unless fileName is None, in which case user is querried
        for all settings
        returns True if settings were loaded
        """
        fileErr = False
        if fileName is not None:
            self.filename = fileName
            try:
                with open (filename, 'r') as fp:
                    data = fp.read()
                    data=data.replace('\n', ',')
                    configDict = json.loads(data)
                    fp.close()
                for key in configDict:
                    setattr (self, key, configDict.get(key))
                #print (self.__dict__)
            except (TypeError, IOError, ValueError) as e: #we will make a file if we didn't find it, or if it was incomplete
                print ('Unable to open and load task configuration:' + str (e) + '\n let\'s configure a new task.\n')
                fileErr = True
        # check for any missing settings, all settings will be missing if making a new config, and call setting functions for
        # things like head fixer that are subclassable need some extra work , when either loaded from file or user queried
        ########## cage specific hardware settings #################################
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
        if not hasattr (self, 'rewardPin'):
            self.rewardPin = int (input('Enter the GPIO pin used by the water delivery solenoid:'))
            fileErr = True
        if not hasattr (self, 'serialPort'):
            self.serialPort = input ('Enter serial port for tag reader(likely either /dev/Serial0 or /dev/ttyUSB0):')
            fileErr = True
        if not hasattr (self, 'TIRpin'):
            self.TIRpin = int (input('Enter the GPIO pin connected to the Tag-In-Range pin on the Tag Reader:'))
            fileErr = True
        if not hasattr (self, 'contactPin') or not hasattr (self, 'contactPolarity') or not hasattr (self, 'contactPUD'):
            self.contactPin = int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:'))
            fileErr = True
            tempInput = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
            if tempInput == 0:
                self.contactPolarity = 'FALLING'
            else:
                self.contactPolarity = 'RISING'
            tempInput = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
            if tempInput == 0:
                self.contactPUD = 'PUD_OFF'
            elif tempInput == 1:
                self.contactPUD = 'PUD_DOWN'
            else:
                self.contactPUD='PUD_UP'
            fileErr = True
        if not hasattr (self, 'LEDpin'):
            self.LEDpin = int (input ('Enter the GPIO pin connected to the blue LED for camera illumination:'))
            fileErr = True
        if not hasattr (self, 'hasLickDetector') or not hasattr (self, 'lickDetectorIRQ'):
            tempInput = input ('Does this setup have a Lick Detector installed? (Y or N)')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasLickDetector = True
                self.lickDetectorIRQ = int (input ('Enter the GPIO pin connected to the IRQ pin for the Lick Detector'))
            else:
                self.hasLickDetector = False
                self.lickDetectorIRQ = 0
            fileErr = True
        if not hasattr (self, 'hasEntryBB') or not hasattr (self, 'entryBBpin'):
            tempInput = input ('Does this setup have a beam break installed at the tube enty way? (Y or N)')
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.hasEntryBB = True
                self.entryBBpin = int (input ('Enter the GPIO pin connected to the entry beam break'))
            else:
                self.hasEntryBB = False
                self.entryBBpin = 0
            fileErr = True
         ####### settings for experiment configuration ########  
        if not hasattr (self, 'cageID'):
            self.cageID = input('Enter a name for the cage ID:')
            fileErr = True
        if not hasattr (self, 'dataPath'):
            self.dataPth = input ('Enter the path to the directory where the data will be saved:')
            fileErr = True
        if not hasattr (self, 'mouseConfigPath'):
            self.mouseConfigPath = input ('Enter the path to the directory where mouse configuration data can be loaded:')
        ################################ Stimulator class makes its own dictionary #######################
        if not hasattr (self, 'StimulatorClass') or not hasattr (self, 'StimulatorDict'):
            self.StimulatorClass = AHF_Stimulator.get_Stimulator_from_user ()
            self.StimulatorDict = AHF_Stimulator.get_class(self.StimulatorClass).config_user_get ()
            fileErr = True
            #### the reward and head-fix proportion settings can also be set on a per-mouse bassis
            ### these provide default values
        if not hasattr (self, 'entranceRewardTime'):
            self.entranceRewardTime = float (input ('Enter solenoid opening duration, in seconds, for entrance rewards:'))
            fileErr = True
        if not hasattr (self, 'taskRewardTime'):
            self.taskRewardTime = float (input ('Enter solenoid opening duration,in seconds, for task rewards:'))
            fileErr = True
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
        ############################ text messaging using textbelt service ############################
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
        ####################################### UDP triggers for alerting other computers ######################3
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
        ############################################ Camera makes its own dictionary of settings #################
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
        # if some of the paramaters were set by user, give option to save
        if fileErr: 
            response = input ('Save new/updated settings to a task configuration file?')
            if response [0] == 'y' or response [0] == 'Y':
                self.saveSettings ()
                
                
    def saveSettings(self):
        """
        Saves current configuration stored in the task object into AHFtask_*.jsn
        Call this function after modifying the contents of the task to save your changes

        :param: none
        :returns: nothing
        """
        # get name for new config file and massage it a bit
        if self.fileName != '':
            inputStr = 'Enter a name to save task settings, or enter to use current name, \'' + self.fileName + '\':'
            newConfig = input (inputStr)
            if newConfig == '':
                configFile = self.fileName
        else:
            newConfig = input ('Enter a name to save task settings as file:')
            # file name passed in may or may not start with AFHconf_ and end with .jsn
            if newConfig.startswith ('AHFconf_'):
                startStr = ''
            else:
                startStr = 'AHFconf_'
            if newConfig.endswith ('.jsn'):
                endStr = ''
            else:
                endStr = '.jsn'
            configFile = startStr + ''.join([c for c in newConfig if c.isalpha() or c.isdigit() or c=='_']) + endStr
        task.fileName = configFile
        # make a dictionary of pretty much all attributes and write it to disk with json dmps
        jsonDict = {}
        for key, value in self.__dict__ :
            if key.startswith ('_') is False and inspect.isroutine (getattr (task,key)) is False:
                jsonDict.update({key: value})

        with open (configFile, 'w') as fp:
            fp.write (json.dumps (jsonDict))
            fp.close ()
            uid = pwd.getpwnam ('pi').pw_uid
            gid = grp.getgrnam ('pi').gr_gid
            os.chown ('AHFconfig.jsn', uid, gid) # we may run as root for pi PWM, so we need to expicitly set ownership



    def showSettings (self):
        ii = 0
        for key, value in inspect.getmembers(self):
            if key.startswith ('_') is False and inspect.isroutine (getattr (self, key)) is False:
                print(ii, ')\t', key, ' = ', value)

    


if __name__ == '__main__':
    task = Task (None)
    task.showSettings()


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

