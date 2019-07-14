#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Stimulator import AHF_Stimulator
from AHF_Mouse import Mouse
import AHF_ClassAndDictUtils as CAD
from time import time, localtime, sleep
from datetime import datetime

class AHF_Stimulator_Rewards (AHF_Stimulator):
    """
    A simple stimulator that just gives a reward every few seconds
    """
    nRewardsDefault = 5
    rewardIntervalDefault = 5.0

    @staticmethod
    def about ():
        return 'A simple stimulator that just gives a reward every few seconds'
    
    @staticmethod
    def dict_from_user (stimDict = {}):
        """
        Querries user for number of rewards and interval between rewards and stores info in a dictionary

        :param stimDict: a starter dictionary that may contain values already, or be empty
        :returns: stimDict dictionary, with edited or appended results from user
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
        self.nRewards = self.expSettings.stimDict.get('nRewards')
        self.rewardInterval = self.expSettings.stimDict.get ('rewardInterval')
        self.rewardTimes = []


    def configStim (self, mouse):
        """
        Makes a local reference to the current mouse
        :param mouse: a reference ot the mouse currently head fixed
        :returns: a string for movie file naming
        """
        self.mouse = mouse
        return 'reward'


    def run(self):
        """
        gives nRewards, one every rewardInterval seconds, as set in stimDict
        """
        self.rewardTimes = []
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(self.rewardInterval)
         # update tally of head fix rewards given in this mouse's stimResultsDict
        HFrewards = self.mouse.stimResultsDict.get('HFrewards', 0)
        self.mouse.stimResultsDict.update ({'HFrewards' : HFrewards + self.nRewards})


    def logfile (self):
        """
        prints to the log file and the shell the time of each reward given
        """
        for rewardTime in self.rewardTimes:
            isoForm = datetime.fromtimestamp(int (rewardTime)).isoformat (' ')
            # print mouse, time stamp, event, formatted time to the log file
            if self.expSettings.logFP != None:
                self.expSettings.logFP.write('{:013}\t{:.2f}\tHeadFixReward\t{:s}\n'.format (self.mouse.tag, rewardTime,isoForm))
            # print mouse, formatted time, event to the shell
            print ('{:013}\t{:s}\tHeadFixReward'.format (self.mouse.tag, isoForm))
        if self.expSettings.logFP != None:
            self.expSettings.logFP.flush()


    def nextDay (self, mice):
        """
        zeros for each mouse the daily tallies of headFix rewards given
        
        :param mice: the mice
        """
        for mouse in mice.generator():
            mouse.stimResultsDict.update ({'HFrewards' : 0})
            mouse.updateStats (self.expSettings.statsFP)