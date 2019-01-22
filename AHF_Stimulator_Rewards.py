#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Stimulator import AHF_Stimulator
from AHF_Mouse import Mouse

from time import time, localtime,timezone, sleep
from datetime import datetime

class AHF_Stimulator_Rewards (AHF_Stimulator):

    @staticmethod
    def about():
        return 'Rewards stimulator gives periodic rewards, no interaction required.'


    @staticmethod
    def config_user_get ():
        nRewards = int (input('Enter the number of rewards you want to give per head fixing session:'))
        rewardInterval = float (input ('Enter the time interval between rewards:'))
        return {'nRewards' : nRewards, 'rewardInterval' : rewardInterval}
    
    
    def __init__ (self, taskP):
        self.task = taskP
        self.stimDict = taskP.StimulatorDict
        self.nRewards = int (self.stimDict.get('nRewards', 5))
        self.rewardInterval = float (self.stimDict.get ('rewardInterval', 2.5))
        self.setup()

        
    def setup (self):
        print ('Rewards stimulator has no hardware setup to do.')


                
    def configStim (self, mouse):
        print ('no config here for rewards')
        return 'stim'

    def run(self):
        timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
        self.rewardTimes = []
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(timeInterval)
        self.mouse.headFixRewards += self.nRewards
        
    def logFile (self):
        event = '\treward'
        mStr = '{:013}'.format(self.mouse.tag) + '\t'
        for rewardTime in self.rewardTimes:
            outPutStr = mStr + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + event
            print (outPutStr)
        if self.textfp != None:
            for rewardTime in self.rewardTimes:
                outPutStr = mStr + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + "\t" + '{:.2f}'.format (rewardTime)  + event
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
            Called before AutoHEadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        pass


    def hardwareTest (self, task):
        pass


"""
if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        GPIO.setmode(GPIO.BCM)
        rewarder = AHF_Rewarder (30e-03, 24)
        rewarder.addToDict ('task', 50e-03)
        thisMouse = Mouse (2525, 0,0,0,0)
        #stimFile = AHF_Stimulator.get_stimulator ()
        #stimulator = AHF_Stimulator.get_class (stimFile)(stimdict, rewarder, None)
        stimdict = {'nRewards' : 5, 'rewardInterval' : .25}
        #stimdict = AHF_Stimulator.configure({})
        #print ('stimdict:')
        #for key in sorted (stimdict.keys()):
        #   print (key + ' = ' + str (stimdict[key]))
        stimulator = AHF_Stimulator_Rewards (stimdict, rewarder, None)
        print (stimulator.configStim (thisMouse))
        stimulator.run ()
        stimulator.logfile()
        thisMouse.show()
    except FileNotFoundError:
        print ('File not found')
    finally:
        GPIO.cleanup ()
"""    

    
