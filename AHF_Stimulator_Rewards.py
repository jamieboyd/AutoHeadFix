#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse

from time import time, localtime,timezone, sleep
from datetime import datetime

class AHF_Stimulator_Rewards (AHF_Stimulator):
    """
    A simple stimulator that just gives a reward every few seconds
    """
    nRewardsDefault = 5
    rewardIntervalDefault = 5.0
    
    @staticmethod
    def dict_from_user (stimDict = {}):
        nRewards = stimDict.get('nRewards', AHF_Stimulator_Rewards.nRewardsDefault)
        tempInput = input ('set number of rewards (currently {:d}) to:'.format (nRewards))
        if tempInput != '':
            nRewards = int (tempInput)
            stimDict.update({'nRewards' : nRewards})
        rewardInterval = stimDict.get('rewardInterval', AHF_Stimulator_Rewards.rewardIntervalDefault)
        tempInput = input ('set reward Interval (currently {:.3f} seconds) to:'.format (rewardIntervalDefault))
        if tempInput != '':
            rewardInterval = float (tempInput)
        if not 'rewardInterval' in stimDict:
            stimDict.update ({'rewardInterval' : rewardInterval})

    def setup (self):
        """
        No harware setup needed, just make local references of nRewards and interval, for ease of use
        The init function will have copied a local reference to confifuration settings dictionary 
        """
        self.nRewards = self.configDict.get('nRewards')
        self.rewardInterval = self.configDict.get ('rewardInterval')
        self.rewardTimes = []


    def configStim (self, mouse):
        if 'HFrewards' in mouse.stimResultsDict:
            mouse.stimResultsDict.update ({'HFrewards' : mouse.stimResultsDict.get('HFrewards') + self.nRewards})
        else:
            mouse.stimResultsDict.update({'HFrewards' : self.nRewards})

        self.mouse = mouse
        return 'stim'

    
    def run(self):
        timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
        self.rewardTimes = []
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(timeInterval)
        self.mouse.headFixRewards += self.nRewards


    def logfile (self):
        event = '\tHeadFixReward'
        mStr = '{:013}\t'.format(self.mouse.tag)
        for rewardTime in self.rewardTimes:
            
            outPutStr = mStr + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + event
            print (outPutStr)
        if self.expSettings.textfp != None:
            for rewardTime in self.rewardTimes:
                outPutStr = mStr + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + "\t" + '{:.2f}'.format (rewardTime)  + event
                self.textfp.write(outPutStr + '\n')
            self.textfp.flush()


    def tester(self,expSettings):
        #Tester function called from the hardwareTester. Includes Stimulator
        #specific hardware tester.
        while(True):
            inputStr = input ('a= camera/LED, q= quit: ')
            if inputStr == 'a':
                #Display preview and turn on LED
                self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
                GPIO.output(self.cageSettings.ledPin, GPIO.HIGH)
                GPIO.output(self.cageSettings.led2Pin, GPIO.HIGH)
                input ('adjust camera/LED: Press any key to quit ')
                self.camera.stop_preview()
                GPIO.output(self.cageSettings.ledPin, GPIO.LOW)
                GPIO.output(self.cageSettings.led2Pin, GPIO.LOW)
            elif inputStr == 'q':
                break



            

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
    

    
