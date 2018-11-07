#! /usr/bin/python
#-*-coding: utf-8 -*-



"""
The plan is to copy all variables from settings, user, into a single object 
"""
   
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
    Main makes a task, then calls its run method
    """
    def __init__ (self, fileName):
        """
        Initializes a Task object with cage settings and experiment settings
        """
        # cage settings from ./AHF_Config.jsn, only 1 of these, load it or query user if it does not exist or is incomplete
        try:
            with open ('AHFconfig.jsn', 'r') as fp:
                data = fp.read()
                data=data.replace('\n', ',')
                configDict = json.loads(data);print (configDict)
                fp.close()
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
                if configDict.get('lick IRQ Pin') is not None:
                    self.lickIRQ = configDict.get('lick IRQ Pin')
                self.dataPath = configDict.get('Path to Save Data')
                self.mouseConfigPath = configDict.get('Path to Mouse Config Data')
                if configDict.get('Entry Beam Break Pin') is not None:
                    self.entryBBpin = configDict.get('Entry Beam Break Pin')
        except (TypeError, IOError) as e: #we will make a file if we didn't find it, or if it was incomplete
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
        """
        Saves current configuration stored in the task object into the file ./AHFconfig.jsn
        Call this function after modifying the contents of the task to save your changes

        :param: none
        :returns: nothing
        """
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
        """
        Prints the current configuration stored in this AHF_CageSet to the console, nicely formatted

        :param: none
        :returns: nothing
        """
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
        """
        Allows the user to edit and save the cage settings
        """
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
        with open (file, 'r') as fp:
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

