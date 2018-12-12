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
from AHF_Camera import AHF_Camera



def load (task, fileName):
    """
    Makes a new settings object, loading from a given file, letting user choose from existing files, or making new settings from user

    Will try to load a file if file name is passed in,
    """
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
        load (task, fileName)
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
            config_from_user(task)
            save(task)
        else:
            # file list starts with a separator (\n) so we split the list on \n and get fileNum + 1
            # each list item starts with fileNum: so split the list item on ":" and get item 1 to get file name
            load (task, (files.split('\n')[fileNum + 1]).split (':')[1])


def config_from_user (task):
    """
    Queries the user for settings. This function may run before a camera or stimulator has been configured

    We need to run static function for stimulator configuration and camera configuration
    """
    task.fileName = ''
    # solenoid opening times, for entry rewards and task rewards, and other reward related settings
    task.entranceRewardTime = float (input ('Solenoid opening duration, in seconds, for entrance rewards:'))
    task.taskRewardTime= float (input ('Solenoid opening duration,in seconds, for task rewards:'))
    task.maxEntryRewards = int (input ('Maximum number of entry rewards that will be given per day:'))
    task.entryRewardDelay = float (input('Delay, in seconds, before an entrance reward is given:'))
    # head fix related settings
    task.propHeadFix = float (input('proportion (0 to 1) of trials that are head-fixed:'))
    task.propHeadFix = min (1, max (0, self.propHeadFix)) # make sure proportion is bewteen 0 and 1
    task.skeddadleTime = float (input ('Time, in seconds, for mouse to get head off the contacts when session ends:'))
    tempInput = input ('Send text messages if mouse exceeds criterion time in chamber?(Y or N):')

    task.hasTextMsg = bool(tempInput [0] == 'y' or tempInput [0] == 'Y')
    if task.hasTextMsg == True:
        task.inChamberTimeLimit = float (input ('In-Chamber duration limit, seconds, before stopping head-fix trials and sending text messg:'))
        task.phoneList =tuple (input('Phone numbers to receive a text message if mouse is in chamber too long:').split(','))
    else:
        task.inChamberTimeLimit = float(input('In-Chamber duration limit, seconds, before stopping head-fix trials:'))
   # Camera related settings, in a dictionary, static function, don't need a camera object to be created
    task.camParamsDict = AHF_Camera.dict_from_user ({})
    # UDP stuff - make a tuple of IP address of other computers
    tempInput = input ('Send UDP triggers to start secondary cameras (Y or N):')
    task.hasUDP = bool(tempInput [0] == 'y' or tempInput [0] == 'Y')
    if task.hasUDP == True:
        task.UDPList =tuple (input('IP addresses of Pis running secondary cameras:').split (','))
        task.cameraStartDelay = float (input ('Delay in seconds between sending UDP and toggling blue LED.'))
    # Stimulator class
    task.stimulator = AHF_Stimulator.get_stimulator_from_user ()
    # static function to make a configration without needing a stimulator to configure it
    task.stimDict = AHF_Stimulator.get_class(task.stimulator).dict_from_user({})


def save (task):
    """
    Saves current settings to a dictionary and then sends dictionary to a json dictionary file

    """
    # get name for new config file and massage it a bit
    if task.fileName != '':
        newConfig = input ('Enter a name to save config, or enter to use current name, \'' + task.fileName + '\':')
        if newConfig == '':
            newConfig = task.fileName
    else:
        newConfig = input ('Enter a name to save config as file:')
    if newConfig != task.fileName:
        newConfig = 'AFHexp_' + ''.join([c for c in newConfig if c.isalpha() or c.isdigit() or c=='_']) + '.jsn'
        task.fileName = newConfig
    # make a dictionary from configuration
    configDict = {}
    configDict['entranceRewardTime'] = task.entranceRewardTime
    configDict['taskRewardTime']= task.taskRewardTime
    configDict['maxEntryRewards'] = task.maxEntryRewards
    configDict['entryRewardDelay'] = task.entryRewardDelay
    configDict['propHeadFix'] = task.propHeadFix
    configDict['skeddadleTime'] = task.skeddadleTime
    configDict['hasTextMsg'] = task.hasTextMsg
    if task.hasTextMsg == True:
        configDict['inChamberTimeLimit'] = task.inChamberTimeLimit
        configDict['phoneList'] = task.phoneList
    configDict['hasUDP'] = task.hasUDP
    if task.hasUDP == True:
        configDict['UDPList']=task.UDPList
        configDict['cameraStartDelay'] = task.cameraStartDelay
    configDict['camParams'] = task.camParamsDict
    configDict['stimulator'] = task.stimulator
    configDict['stimParams'] = task.stimDict


    # open the file name
    with open (newConfig, 'w') as fp:
        fp.write (json.dumps (configDict))
        fp.close ()
        uid = pwd.getpwnam ('pi').pw_uid
        gid = grp.getgrnam ('pi').gr_gid
        os.chown (newConfig, uid, gid) # we run AutoHeadFix as root for GPIO, so expicitly set ownership for easy editing


def load (self, file):
    with open (file, 'r') as fp:
        configDict = json.loads(fp.read())
        fp.close()
        self.fileName = file
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

    user can either change the stimulaotr, or reconfigure it, but not both
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
        else:
            print("Key hasn't been added to the editor... Please contact Dr. Yuri Nater for help.")
    return editVal


## for testing purposes
if __name__ == '__main__':
    settings = AHF_Settings (None)
    settings.edit_from_user()
    settings.show()
