#! /usr/bin/python
#-*-coding: utf-8 -*


from AHF_Rewarder import AHF_Rewarder
from AHF_LickDetector import AHF_LickDetector
from AHF_Mouse import Mouse
import time
import json
import os
from time import time, sleep
from datetime import datetime

class AHF_Stimulator (object):

    """
    Stimulator does all stimulation and reward during a head fix task

    All events and their timings in a head fix, including rewards, are controlled by a Stimulator.

    """

    def __init__ (self, cageSettings, configDict, rewarder, lickDetector, textfp, camera):
        """
        The Stimulator class is inited with: a config dictionary of settings; the same rewarder
        object used to give entry rewards; and a file pointer to the log file
        """
        self.rewarder = rewarder
        self.textfp = textfp
        self.lickDetector = lickDetector
        self.camera = camera
        self.cageSettings = cageSettings
        self.mouse = None
        if configDict == None:
            self.config_from_user ()
        else:
            self.configDict = configDict
        self.setup()

    def setup (self):
        pass

    def change_config (self, changesDict):
        """
        Edits the configuration dictionary, adding or replacing with key/value pairs from changesDict paramater

        """
        for key in sorted (changesDict.keys()):
            self.configDict.update({key : changesDict.get (key)})



    def config_from_user (self):
        """
            makes or edits the dictionary object that holds settings for this  stimulator

            Gets info from user with the input function, which returns strings
            so your sublass methods will need to use int() or float() to convert values as appropriate
        """
        if self.configDict is not None and len (self.configDict.keys()) > 0:
            for key in sorted (self.configDict.keys()):
                tempInput = input ('set ' + key + '(currently ' + str (self.configDict[key]) + ') to :')
                if tempInput != '':
                    self.configDict[key] = tempInput
        else:
            print ('starting with a new empty dictionary...')
            self.configDict = {}
        while True:
            key = input ('Enter a new Key, or -1 to quit:')
            if key == '-1' or key == '':
                break
            else:
                value = input ('Enter a value for ' + key + ':')
                self.configDict.update({key : value})



    def configStim (self, mouse):
        """
        Called before running each head fix trial, stimulator decides what to do and configures itself

        You may wish to different things for different mice, and to store data about stim presentations in the mouse object
        returns: a short string representing stim configuration, used to generate movie file name
        :param mouse: the object representing the mouse that is currently head-fixed
        """
        if 'stimCount' in mouse.stimResultsDict:
            mouse.stimResultsDict.update ({'stimCount' : mouse.stimResultsDict.get('stimCount') + 1})
        else:
            mouse.stimResultsDict.update({'stimCount' : 1})

        self.mouse = mouse
        return 'stim'


    def run (self):
        """
        Called at start of each head fix. Gives a reward, increments mouse's reward count, then waits 10 seconds
        """
        self.rewarder.giveReward ('task')
        self.mouse.headFixRewards += 1
        sleep (10)

    def logFile (self):
        """
            Called after each head fix, prints more detailed text to the log file, perhaps a line for each event

           You may wish to use the same format as writeToLogFile function in __main__.py

           Or you may wish to override with pass and log from the run method
        """

        event = 'stim'
        mStr = '{:013}'.format(self.mouse.tag) + '\t'
        outPutStr = mStr + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
        print (outPutStr)
        if self.textfp != None:
            outPutStr = mStr + '{:.2f}'.format (time ()) + '\t' + event
            self.textfp.write(outPutStr + '\n')
            self.textfp.flush()


    def nextDay (self, newFP):
        """
            Called when the next day starts. The stimulator is given the new log file pointer. Can do other things as needed
            :param newFP: the file pointer for the new day's log file
        """
        self.textfp = newFP


    def quitting (self):
        """
            Called before AutoHeadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        pass

    def tester (self,expSettings):
        """
            Tester function called from the hardwareTester. Includes Stimulator
            specific hardware tester.
        """
        pass

    def inspect_mice (self,mice,cageSettings,expSettings):
        """
            Helper function to show stimulator specific mouse data.
        """
        pass

    def h5updater (self,mouse,h5):
        """
            updates stimulator specific data to h5 file
        """
        pass

    @staticmethod
    def get_class(fileName):
        """
        Imports a module from a fileName (stripped of the .py) and returns the class

        Assumes the class is named the same as the module
        """
        module = __import__(fileName)
        return getattr(module, fileName)


    @staticmethod
    def get_stimulator_from_user ():
        """
        Static method that trawls through current folder looking for stimulator class python files

        Allows user to choose from the list of files found. Files are recognized by names starting
        with 'AHF_Stimulator_' and ending with '.py'
        Raises: FileNotFoundError if no stimulator class files found
        """
        iFile=0
        files = ''
        for f in os.listdir('.'):
            if f.startswith ('AHF_Stimulator') and f.endswith ('.py'):
                if iFile > 0:
                    files += ';'
                files += f
                iFile += 1
        if iFile == 0:
            print ('Could not find an AHF_Stimulator_ file in the current or enclosing directory')
            raise FileNotFoundError
        else:
            if iFile == 1:
                print ('Stimulator file found: ' + stimFile)
                stimFile =  files.split('.')[0]
            else:
                inputStr = '\nEnter a number from 0 to ' + str (iFile -1) + ' to Choose a Stimulator class:\n'
                ii=0
                for file in files.split(';'):
                    inputStr += str (ii) + ': ' + file + '\n'
                    ii +=1
                inputStr += ':'
                stimFileNum = -1
                while stimFileNum < 0 or stimFileNum > (iFile -1):
                    stimFileNum =  int(input (inputStr))
                stimFile =  files.split(';')[stimFileNum]
                stimFile =  stimFile.split('.')[0]
            return stimFile

    @staticmethod
    def dict_from_user (stimDict):
        """
            static method that makes or edits a dictionary object that holds settings for a stimulator

            configure gets info from user with the input function, which returns strings
            so your sublass methods will need to use int() or float() to convert values as appropriate
        """
        if stimDict is not None and len (stimDict.keys()) > 0:
            for key in sorted (stimDict.keys()):
                tempInput = input ('set ' + key + '(currently ' + str (stimDict[key]) + ') to :')
                if tempInput != '':
                    stimDict[key] = tempInput
        else:
            print ('starting with a new empty dictionary...')
            stimDict = {}
        while True:
            key = input ('Enter a new Key, or -1 to quit:')
            if key == '-1' or key == '':
                break
            else:
                value = input ('Enter a value for ' + key + ':')
                stimDict.update({key : value})
        return stimDict


if __name__ == '__main__':
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    rewarder = AHF_Rewarder (30e-03, 24)
    rewarder.addToDict ('task', 50e-03)
    thisMouse = Mouse (2525, 0,0,0,0, '')
    stimFile = AHF_Stimulator.get_stimulator_from_user ()
    stimDict = AHF_Stimulator.get_class (stimFile).dict_from_user({})
    stimulator = AHF_Stimulator.get_class (stimFile)(stimDict, rewarder, None)
    print (stimulator.configStim (thisMouse))
    stimulator.run ()
    stimulator.logFile()
    stimulator.config_from_user()
    print (stimulator.configStim (thisMouse))
    stimulator.run ()
    stimulator.logFile()
    thisMouse.show()
    GPIO.cleanup ()
