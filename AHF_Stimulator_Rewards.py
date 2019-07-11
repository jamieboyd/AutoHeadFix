#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse

from time import time, localtime, sleep
from datetime import datetime

class AHF_Stimulator_Rewards (AHF_Stimulator):
    """
    A simple stimulator that just gives a reward every few seconds
    """
    nRewardsDefault = 5
    rewardIntervalDefault = 5.0
    
    @staticmethod
    def dict_from_user (stimDict = {}):
        """
        Querries user for number of rewards and interval between rewards and stores info in a dictionary

        :param stimDict: a starter dictionary that may contain values already, or be empty
        :returns stimDict dictionary, with edited or appended results from user
        """
        nRewards = stimDict.get('nRewards', AHF_Stimulator_Rewards.nRewardsDefault)
        tempInput = input ('set number of rewards (currently {:d}) to:'.format (nRewards))
        if tempInput != '':
            nRewards = int (tempInput)
            stimDict.update({'nRewards' : nRewards})
        rewardInterval = stimDict.get('rewardInterval', AHF_Stimulator_Rewards.rewardIntervalDefault)
        tempInput = input ('set reward Interval (currently {:.2f} seconds) to:'.format (AHF_Stimulator_Rewards.rewardIntervalDefault))
        if tempInput != '':
            rewardInterval = float (tempInput)
        if not 'rewardInterval' in stimDict:
            stimDict.update ({'rewardInterval' : rewardInterval})
        return stimDict
    
    def setup (self):
        """
        No harware setup needed, just make local references of nRewards and interval, for ease of use
        
        The init function will have copied a local reference to configuration settings dictionary 
        """
        self.nRewards = self.configDict.get('nRewards')
        self.rewardInterval = self.configDict.get ('rewardInterval')
        self.rewardTimes = []


    def configStim (self, mouse):
        self.mouse = mouse
        return 'stim'

    
    def run(self):
        self.rewardTimes = []
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(self.rewardInterval)
         # update tally of head fix rewards given in this mouses stimResultsDict
        HFrewards = mouse.stimResultsDict.get('HFrewards', 0)
        mouse.stimResultsDict.update ({'HFrewards' : HFrewards + self.nRewards})



    def logfile (self):
        """
        prints to the log file and the shell the time of each reward given
        """
        for rewardTime in self.rewardTimes:
            # print mouse, time stamp, event, formatted time to the log file
            if self.expSettings.textfp != None:
                self.textfp.write('{:013}\t{:.2f}\tHeadFixReward\t{:s}\n'.format (self.mouse.tag, rewardTime, int (rewardTime)).isoformat (' '))
            # print mouse, formatted time, event to the shell
            print ('{:013}\t{:s}\tHeadFixReward'.format (self.mouse.tag, int (rewardTime)).isoformat (' '))
        if self.expSettings.textfp != None:
            self.textfp.flush()


    def nextDay (self, newFP, mice):
        self.textfp = newFP
        for mouse in mice.generator():
            mouse.stimResultsDict.update ({'HFrewards' : 0})
            mouse.updateStats (newFP)


    def tester(self):
        """
        Tester function to be called from the hardwareTester
        makes a sample mouse and calls the run function in a loop, giving option to change settings every time
        """
        self.configStim (Mouse (2525, 0,0,0,{}))
        while True:
            response = input ('change stimulus settings (yes or no)?')
            if response [0] == 'Y' or response [0] == 'y':
                self.stimDict = AHF_Stimulator.Edit_Dict (self.stimDict, 'Rewards Stimulator')
                self.setup ()
            response = input ('run stimulator as configured (yes or no)?')
            if response [0] == 'Y' or response [0] == 'y':
                self.run ()
                self.logfile()
                self.mouse.show()


    
