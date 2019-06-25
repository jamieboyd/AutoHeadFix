#! /usr/bin/python
#-*-coding: utf-8 -*-

"""
AHF_Settings provides functions to read, edit, and save settings for the AutoheadFix program
"""

import os
import sys
import json
import pwd
import grp

from AHF_Stimulator import AHF_Stimulator
from AHF_Stimulator_Rewards import AHF_Stimulator_Rewards
from AHF_Camera import AHF_Camera

class AHF_Settings (object):
    """
    AHF_Settings is a class that loads, edits, and saves settings for the AutoheadFix program
    It keeps the information in a dictionary, as well as in instance variables
    """
    # define some mostly useful defaults - hard to do for phone numbers and i.p addresses
    entranceRewardTimeDef = 0.3
    taskRewardTimeDef = 0.6
    maxEntryRewardsDef = 100
    entryRewardDelayDef = 1
    propHeadFixDef = 1.0
    skeddadleTimeDef = 0.75
    inChamberTimeLimitDef = 600
    hasTextMsgDef = False
    phoneListDef = ('15555555555','15555555555')
    textBeltKeyDef = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    hasUDPDef = True
    UDPListDef=('127.0.0.1','127.0.0.1')
    cameraStartDelayDef = 3
    stimulatorDef = 'Rewards'
    stimDictDef = {'nRewards' : AHF_Stimulator_Rewards.nRewardsDefault, 'rewardInterval' : AHF_Stimulator_Rewards.rewardIntervalDefault}
    camParamsDictDef = {'format': 'rgb', 'framerate': 30.0, 'shutter_speed': 30000, 'previewWin': (0, 0, 256, 256), 'quality': 20, 'whiteBalance': False, 'resolution': (256, 256), 'iso': 400}


    @staticmethod
    def get_SettingsFile_from_user ():
        """
        Static method that trawls through current folder looking for AHF_settings .jsn files from which user chooses one
        
        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_Settings_' and ending with '.jsn'
        Raises: FileNotFoundError if no stimulator class files found
        Returns: name of the file the user chose, stripped of AHF_Settings and .jsn, or empty sting if no files found, or user wants new config
        """
        fileList = []
        startlen = 13
        endlen =4
        for f in os.listdir('.'):
            if f.startswith ('AHF_Settings_') and f.endswith ('.jsn'):
                fname = f[startlen :-endlen]
                fileList.append (fname)
        if len (fileList) == 0:
            print ('Could not find an AHF_Settings file in the current or enclosing directory.')
            return ''
        else:
            inputStr = '\nEnter a number from 1 to {} to choose a Settings file, or 0 to make new settings:\n'.format(len (fileList))
            ii=0
            for file in fileList:
                inputStr += '{:d} : {:s}\n'.format((ii + 1), file)
                ii +=1
            inputStr += ':'
            response = -1
            while response < 0 or response > len(fileList):
                response =  int(input (inputStr))
            if response ==0:
                return ''
            else:
                return fileList[response -1]



    def __init__ (self, fileNameP = ''):
        """
        Makes a new settings object, loading from a given file, letting user choose from existing files, or making new settings from user

        Will try to load a file if file name is passed in, else will get user to select a file
        """
        hasFile = True
        if fileNameP == '':
            fileNameP = AHF_Settings.get_SettingsFile_from_user ()
            if fileNameP == '':
                hasFile = False
        # if we have a file, try to load it
        if hasFile:
            # fileName may be stripped
            if not fileNameP.startswith ('AHF_Settings_'):
                fileNameP = 'AHF_Settings_' + fileNameP
            if not fileNameP.endswith ('.jsn'):
                fileNameP = fileNameP + '.jsn'
            hasFile = False
            for file in os.listdir('.'):
                if file == fileNameP:
                    hasFile = True
                    break
            if hasFile:
                try:
                    fp = open (fileNameP, 'r')
                    data = fp.read()
                    fp.close()
                    data= data.replace('\n', ",")
                    self.settingsDict = json.loads(data)
                    self.entranceRewardTime = self.settingsDict.get ('entranceRewardTime', AHF_Settings.entranceRewardTimeDef)
                    self.taskRewardTime = self.settingsDict.get ('taskRewardTime', AHF_Settings.taskRewardTimeDef)
                    self.maxEntryRewards = self.settingsDict.get ('maxEntryRewards', AHF_Settings.maxEntryRewardsDef)
                    self.entryRewardDelay = self.settingsDict.get('entryRewardDelay', AHF_Settings.entryRewardDelayDef)
                    self.propHeadFix = self.settingsDict.get('propHeadFix', AHF_Settings.propHeadFixDef)
                    self.skeddadleTime = self.settingsDict.get ('skeddadleTime', AHF_Settings.skeddadleTimeDef)
                    self.inChamberTimeLimit = self.settingsDict.get ('inChamberTimeLimit',AHF_Settings.inChamberTimeLimitDef)
                    self.hasTextMsg = self.settingsDict.get ('hasTextMsg', AHF_Settings.hasTextMsgDef)
                    if self.hasTextMsg == True:
                        self.phoneList = self.settingsDict.get('phoneList', AHF_Settings.phoneListDef)
                        self.textbeltKey = self.settingsDict.get ('textBeltKey', AHF_Settings.textBeltKeyDef)
                    self.hasUDP = self.settingsDict.get ('hasUDP', AHF_Settings.hasUDPDef)
                    if self.hasUDP == True:
                        self.UDPList = self.settingsDict.get ('UDPList',AHF_Settings.UDPListDef)
                        self.cameraStartDelay = self.settingsDict.get('cameraStartDelay', AHF_Settings.cameraStartDelayDef)
                    self.camParamsDict = self.settingsDict.get('camParams', AHF_Settings.camParamsDictDef)
                    self.stimDict = self.settingsDict.get('stimParams', AHF_Settings.stimDictDef)
                    self.stimulator = self.settingsDict.get('stimulator', AHF_Settings.stimulatorDef)
                except Exception as e:
                    print ('Could not read data from {:s}: {:s}'.format (file, str (e)))
                    hasFile = False
        # either a file name was nor provided, or file name did not exist, or it could not be loaded
        if not hasFile:
            self.fileName = ''
            self.settingsDict = {}
            # reward settings
            self.entranceRewardTime = AHF_Settings.entranceRewardTimeDef
            tempInput = input ('Solenoid opening duration for entrance rewards, currently {:.3f} seconds:'.format (self.entranceRewardTime))
            if tempInput != '':
                self.entranceRewardTime = float (tempInput)
            self.settingsDict.update({'entranceRewardTime' : self.entranceRewardTime})
            self.taskRewardTime= AHF_Settings.taskRewardTimeDef
            tempInput = input ('Solenoid opening duration for task rewards,currently {:.3f} seconds:'.format (self.taskRewardTime))
            if tempInput != '':
                self.taskRewardTime = float (tempInput)
            self.settingsDict.update({'taskRewardTime' : self.taskRewardTime})
            self.maxEntryRewards = AHF_Settings.maxEntryRewardsDef
            tempInput = input('Maximum number of entry rewards that will be given per day, currently {:d}:'.format (self.maxEntryRewards))
            if tempInput != '':
                self.maxEntryRewards = int (tempInput)
            self.settingsDict.update({'maxEntryRewards' : self.maxEntryRewards})
            # head fix related settings
            self.propHeadFix = AHF_Settings.propHeadFixDef
            tempInput = input ('proportion (0 to 1) of trials that are head-fixed, currently {:.3f}:'.format (self.propHeadFix))
            if tempInput != '':
                self.propHeadFix = float (tempInput)
            self.settingsDict.update({'propHeadFix' : self.propHeadFix})
            self.skeddadleTime = AHF_Settings.skeddadleTimeDef
            tempInput = input ('Time for mouse to get head off the contacts when session ends, currently {:.3f} seconds:'.format (self.skeddadleTime))
            if tempInput != '':
                self.skeddadleTime = float (tempInput)
            self.settingsDict.update({'skeddadleTime' : self.skeddadleTime})
            # in-chamber time limit and text messaging
            self.inChamberTimeLimit = AHF_Settings.inChamberTimeLimitDef
            tempInput = input ('In-Chamber duration limit before stopping head-fix trials, currently {:.3f} seconds:'.format(self.inChamberTimeLimit))
            if tempInput != '':
                self.inChamberTimeLimit = float (tempInput)
            self.settingsDict.update ({'inChamberTimeLimit' : self.inChamberTimeLimit})  
            self.hasTextMsg = AHF_Settings.hasTextMsgDef
            tempInput = input ('Send text messages if mouse exceeds in-Chamber duration limit? (Yes or No) currently {:s}:'.format ('Yes' if self.hasTextMsg else 'No'))
            if tempInput != '':
                self.hasTextMsg = bool(tempInput [0] == 'y' or tempInput [0] == 'Y')
            self.settingsDict.update ({'hasTextMsg' : self.hasTextMsg})
            if self.hasTextMsg == True:                  
                self.phoneList = AHF_Settings.phoneListDef
                tempList = ''
                for ph in self.phoneList:
                    tempList += ',' + ph if tempList != '' else ph
                tempInput = input ('comma-separated list of phone numbers to receive a text message if mouse exceeds in-Chamber duration limit, currently {:s}:'.format (tempList))
                if tempInput != '':
                    self.phoneList =tuple (tempInput.split(','))
                self.settingsDict.update ({'phoneList' : self.phoneList})
                self.textbeltKey = AHF_Settings.textbeltKeyDef
                tempInput = input ('Enter access key for textbelt.com, currently {:s}'.format (self.textbeltKey))
                if tempInput != '':
                    self.textbeltKey = tempInput
                self.settingsDict.update ({'textbeltKey' : self.textbeltKey})
            # UDP stuff - a tuple of IP address of other computers
            self.hasUDP = AHF_Settings.hasUDPDef
            tempInput = input ('Send UDP triggers to start secondary cameras (Yes or No) currently  {:s}:'.format ('Yes' if self.hasUDP else 'No'))
            self.hasUDP = bool(tempInput [0] == 'y' or tempInput [0] == 'Y')
            if self.hasUDP == True:
                self.UDPList = AHF_Settings.UDPListDef
                tempList = ''
                for ip in self.UDPList:
                    tempList += ',' + ip if tempList != '' else ip
                tempInput = input('IP addresses of Pis running secondary cameras, currently {:s}:'.format (tempList))
                if tempInput != '':
                    self.UDPList =tuple (tempInput.split (','))
                self.settingsDict.update ({'UDPList' : self.UDPList})
                self.cameraStartDelay = AHF_Settings.cameraStartDelayDef
                tempInput = input ('Delay between sending UDP and toggling blue LED, currently {:.3f} seconds:'.format (self.cameraStartDelay))
                if tempInput != '': 
                    self.cameraStartDelay = float (tempInput)
                self.settingsDict.update ({'cameraStartDelay' : self.cameraStartDelay})
            # Stimulator file name
            self.stimulator = AHF_Settings.stimulatorDef
            tempInput = input ('Stimulator = {:s}. Select different Stimulator? (Yes or No)'.format (self.stimulator))
            if tempInput [0] == 'y' or tempInput [0] == 'Y':
                self.stimulator = AHF_Stimulator.get_Stimulator_from_user ()
                # static function to make a configration without needing a stimulator to configure it
                self.stimDict = AHF_Stimulator.get_class(self.stimulator).dict_from_user({})
            else:
                


            # Camera related settings, in a dictionary, static function, don't need a camera object to be created
            self.camParamsDict = AHF_Camera.dict_from_user ({})

 

    def save (self):
        """
        Saves current settings to a dictionary and then sends dictionary to a json dictionary file

        """
        # get name for new config file and massage it a bit
        if self.fileName != '':
            newConfig = input ('Enter a name to save config, or enter to use current name, \'' + self.fileName + '\':')
            if newConfig == '':
                newConfig = self.fileName
        else:
            newConfig = input ('Enter a name to save config as file:')
        if newConfig != self.fileName:
            newConfig = 'AFHexp_' + ''.join([c for c in newConfig if c.isalpha() or c.isdigit() or c=='_']) + '.jsn'
            self.fileName = newConfig
        # make a dictionary from configuration
        settingsDict = {}
        settingsDict['entranceRewardTime'] = self.entranceRewardTime
        settingsDict['taskRewardTime']= self.taskRewardTime
        settingsDict['maxEntryRewards'] = self.maxEntryRewards
        settingsDict['entryRewardDelay'] = self.entryRewardDelay
        settingsDict['propHeadFix'] = self.propHeadFix
        settingsDict['skeddadleTime'] = self.skeddadleTime
        settingsDict['hasTextMsg'] = self.hasTextMsg
        if self.hasTextMsg == True:
            settingsDict['inChamberTimeLimit'] = self.inChamberTimeLimit
            settingsDict['phoneList'] = self.phoneList
        settingsDict['hasUDP'] = self.hasUDP
        if self.hasUDP == True:
            settingsDict['UDPList']=self.UDPList
            settingsDict['cameraStartDelay'] = self.cameraStartDelay
        settingsDict['camParams'] = self.camParamsDict
        settingsDict['stimulator'] = self.stimulator
        settingsDict['stimParams'] = self.stimDict


        # open the file name
        with open (newConfig, 'w') as fp:
            fp.write (json.dumps (settingsDict))
            fp.close ()
            uid = pwd.getpwnam ('pi').pw_uid
            gid = grp.getgrnam ('pi').gr_gid
            os.chown (newConfig, uid, gid) # we run AutoHeadFix as root for GPIO, so expicitly set ownership for easy editing






    def show (self):
        """
        Prints the current configuration stored in this AHF_Settings to the console, nicely formatted

           :param: none
           :returns: nothing
        """
        print ('****************Current Auto-Head-Fix experiment Settings********************************')
        print ('1:Entrance Reward Time (secs) =' + str (self.entranceRewardTime))
        print ('2:Task Reward Time (secs) =' +  str (self.taskRewardTime))
        print ('3:Maximum Daily Entry Rewards =' + str (self.maxEntryRewards))
        print ('4:Entry Reward Delay (secs) =' + str (self.entryRewardDelay))
        print ('5:Proportion of Contacts to Head Fix (0-1) =' + str(self.propHeadFix))
        print ('6:Time for Mouse to break contact after trial (secs) =' + str(self.skeddadleTime))
        print ('7:Use Text Messaging =' + str (self.hasTextMsg))
        if self.hasTextMsg == True:
            print ('\t7_a:List of Phone Numbers=' + str(self.phoneList))
            print ('8:Duration in chamber (secs) before stopping trials and sending message =' + str (self.inChamberTimeLimit))
        else:
            print ('8:Duration in chamber (secs) before stopping trials =' + str (self.inChamberTimeLimit))
        print ('9:Send UDP triggers = ' + str (self.hasUDP))
        if self.hasUDP == True:
            print ('\t9_a:List of ip addresses for UDP = ' + str(self.UDPList))
            print ('\t9_b:Camera start to LED ON delay (secs) =' + str (self.cameraStartDelay))
        print ('10:Stimulator = ' + self.stimulator)
        i =0
        for key in sorted (self.stimDict.keys()):
            print ('\t10_' + chr (97 + i) + ": " + key + ' = ' + str (self.stimDict[key]))
            i+=1




    def edit_from_user (self):
        """
        Allows user to edit experiment settings, including stimulator settings, but not camera settings

        user can either change the stimulator, or reconfigure it, but not both
        :returns: code for mods - bit 0 = 1 is set if stimulator config is changed, bit 1 =2 is set if stimulator is changed
        """
        #
        editVal=0
        while True:
            self.show()
            editNum = input ('Enter number of paramater to Edit, or 0 when done:')
            if editNum == '0':
                tempInput = input ('Save configuration to file (Yes or No):')
                if tempInput[0] == 'Y' or tempInput [0] == 'y':
                    self.save ()
                break
            elif editNum == '1':
                self.entranceRewardTime = float (input ('Solenoid opening duration, in seconds, for entrance rewards:'))
            elif editNum == '2':
                self.taskRewardTime= float (input ('Solenoid opening duration,in seconds, for task rewards:'))
            elif editNum == '3':
                self.maxEntryRewards = int (input ('Maximum number of entry rewards that will be given per day:'))
            elif editNum =='4':
                self.entryRewardDelay = float (input('Delay, in seconds, before an entrance reward is given:'))
            elif editNum =='5':
                self.propHeadFix = float (input('proportion (0 to 1) of trials that are head-fixed:'))
                self.propHeadFix = min (1, max (0, self.propHeadFix)) # make sure proportion is bewteen 0 and 1
            elif editNum=='6':
                self.skeddadleTime = float (input ('Time, in seconds, for mouse to get head off the contacts when session ends:'))
            elif editNum =='7':
                tempInput = input ('Send text messages if mouse exceeds criterion time in chamber?(Y or N):')
                self.hasTextMsg = bool(tempInput [0] == 'y' or tempInput [0] == 'Y')
                if self.hasTextMsg == True and self.phoneList == '':
                    self.phoneList =tuple (input('Phone numbers to receive a text message if mouse is in chamber too long:').split(','))
            elif editNum == '7a':
                self.phoneList =tuple (input('Phone numbers to receive a text message if mouse is in chamber too long:').split(','))
            elif editNum == '8':
                self.inChamberTimeLimit = float (input ('Time limit in seconds for mouse being in the chamber before stopping headfixes, optionally sending text mssg:'))
            elif editNum == '9':
                tempInput = input ('Send UDP triggers to start secondary cameras (Y or N):')
                self.hasUDP = bool(tempInput [0] == 'y' or tempInput [0] == 'Y')
                if self.UDPList == True:
                    self.UDPList =tuple (input('IP addresses of Pis running secondary cameras:').split (','))
                    self.cameraStartDelay = float (input ('Delay in seconds between sending UDP and toggling blue LED.'))
            elif editNum == '9a':
                self.UDPList =tuple (input('IP addresses of Pis running secondary cameras:').split (','))
            elif editNum == '9b':
                self.cameraStartDelay = float (input ('Delay in seconds between sending UDP and toggling blue LED.'))
            elif editNum == '10':
                self.stimulator = AHF_Stimulator.get_stimulator_from_user ()
                editVal = editVal | 2
            elif editNum.split('_')[0] == '10':
                editVal = editVal | 1
                selectedKey = ord (editNum.split ('_')[1]) -97
                i=0
                for key in sorted (self.stimDict.keys()):
                    if i==selectedKey:
                        newValue = input ('Set ' + key + ' (currently ' + str (self.stimDict.get(key)) + ') to:')
                        self.stimDict.update ({key : newValue})
                        break
                    i+=1

                print("Key hasn't been added to the editor....")
        return editVal


## for testing purposes
if __name__ == '__main__':
    settings = AHF_Settings (None)
    settings.edit_from_user()
    settings.show()
