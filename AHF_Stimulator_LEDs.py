#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Stimulator import AHF_Stimulator
from AHF_Stimulator_Rewards import AHF_Stimulator_Rewards
from AHF_Mouse import Mouse
import AHF_ClassAndDictUtils as CAD
from time import time, localtime, sleep
from datetime import datetime
from PTSimpleGPIO import PTSimpleGPIO, Train

class AHF_Stimulator_LEDs (AHF_Stimulator_Rewards):
    """
    Stimulator that flashes LEDs for visual stimulation, between giving rewards
    """
    left_led_pinDefault = 17
    center_led_pinDefault = 18
    right_led_pinDefault = 19
    train_frequencyDefault = 10
    train_dutyDefault = 0.5
    train_durationDefault = 2
    
    @staticmethod
    def about ():
        return 'Uses PTSimpleGPIO to interleave flashing of LEDs for visual stimulation with giving of rewards'

    @staticmethod
    def dict_from_user (stimDict = {}):

        left_led_pin = stimDict.get('left_led_pin', AHF_Stimulator_LEDs.left_led_pinDefault)
        tempInput = input ('set GPIO pin number for left LED (currently {:d}) to:'.format (left_led_pin))
        if tempInput != '':
            left_led_pin = int (tempInput)
            stimDict.update({'left_led_pin' : left_led_pin})
        center_led_pin = stimDict.get('center_led_pin', AHF_Stimulator_LEDs.center_led_pinDefault)
        tempInput = input ('set GPIO pin number for centre LED (currently {:d}) to:'.format (center_led_pin))
        if tempInput != '':
            center_led_pin = int (tempInput)
            stimDict.update({'center_led_pin' : center_led_pin})
        right_led_pin = stimDict.get('right_led_pin', AHF_Stimulator_LEDs.right_led_pinDefault)
        tempInput = input ('set GPIO pin number for right LED (currently {:d}) to:'.format (right_led_pin))
        if tempInput != '':
            right_led_pin = int (tempInput)
            stimDict.update({'right_led_pin' : right_led_pin})
        train_frequency = stimDict.get('train_frequency', AHF_Stimulator_LEDs.train_frequencyDefault)
        tempInput = input ('set LED flash frequency (currently {:.2f} Hz) to:'.format (train_frequency))
        if tempInput != '':
            train_frequency = float (tempInput)
            stimDict.update({'train_frequency' : train_frequency})
        train_duty = stimDict.get('train_duty', AHF_Stimulator_LEDs.train_dutyDefault)
        tempInput = input ('set LED duty cycle (currently {:.2f}; keep between 0 and 1) to:'.format (train_duty))
        if tempInput != '':
            train_duty = float (tempInput)
            stimDict.update({'train_duty' : train_duty})
        train_duration = stimDict.get('train_duration', AHF_Stimulator_LEDs.train_durationDefault)
        tempInput = input ('set duration of each train of flashes (currently {:.2f} seconds) to:'.format (train_duration))
        if tempInput != '':
            train_duration = float (tempInput)
            stimDict.update({'train_duration' : train_duration}) 
        # get number of rewards and timing, and hence number of flashes,  from Rewards
        return super(AHF_Stimulator_LEDs, AHF_Stimulator_LEDs).dict_from_user (stimDict)

        
    def setup (self):
        # number of rewards and timing, and hence number of flashes, from Rewards
        super().setup()
        # frequency, dutycycle, and duration of each train
        self.train_frequency =  float (self.expSettings.stimDict.get ('train_frequency'))
        self.train_duty = float (self.expSettings.stimDict.get ('train_duty'))
        self.train_duration = float (self.expSettings.stimDict.get ('train_duration'))
        # 3 leds - left, right, center, controlled by 3 GPIO pins as indicated
        self.left_led_pin = self.expSettings.stimDict.get('left_led_pin')
        self.center_led_pin = self.expSettings.stimDict.get ('center_led_pin')
        self.right_led_pin =  self.expSettings.stimDict.get ('right_led_pin')
        if self.left_led_pin != 0:
            self.leftTrain = Train (PTSimpleGPIO.MODE_FREQ, self.left_led_pin, 0, self.train_frequency,self.train_duty,self.train_duration, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        else:
            self.leftTrain = None
        if self.center_led_pin != 0:
            self.centerTrain = Train (PTSimpleGPIO.MODE_FREQ, self.center_led_pin, 0, self.train_frequency,self.train_duty,self.train_duration, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        else:
            self.centerTrain = None
        if self.right_led_pin != 0:
            self.rightTrain = Train (PTSimpleGPIO.MODE_FREQ, self.right_led_pin, 0, self.train_frequency,self.train_duty,self.train_duration, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        else:
            self.rightTrain = None
        self.rewardTimes = []
        self.flashTimes = []
        self.sleepTime = self.rewardInterval/2
        self.runTrain = None
        self.stimStr = ''


    def configStim (self, mouse):
        self.mouse = mouse
        stimArray = mouse.stimResultsDict.get('LCR', [0,0,0])
        ranVal = random ()
        if ranVal < 0.3333:
            self.runTrain = self.leftTrain
            self.stimStr = ' L'
            stimArray [0] += self.nRewards
        elif ranVal < 0.6666:
            self.runTrain = self.centerTrain
            self.stimStr = 'C'
            stimArray [1] += self.nRewards
        else:
            self.runTrain = self.RightTrain
            self.stimStr = 'R'
            stimArray [2] += self.nRewards
        mouse.stimResultsDict.update ({'LCR' : stimArray})
        return self.stimStr


    def run(self):
        self.rewardTimes = []
        self.flashTimes = []
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep (sleepTime)
            self.flashTimes.append (time())
            self.runTrain.do_train ()
            sleep (sleepTime)
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
        for flashTime in self.flashTimes:
            isoForm = datetime.fromtimestamp(int (flashTime)).isoformat (' ')
            # print mouse, time stamp, event, formatted time to the log file
            if self.expSettings.logFP != None:
                self.expSettings.logFP.write('{:013}\t{:.2f}\tFlash:{:s}\t{:s}\n'.format (self.mouse.tag, self.stimStr, rewardTime, isoForm))
            # print mouse, formatted time, event to the shell
            print ('{:013}\t{:s}\tFlash:{:s}'.format (self.mouse.tag, isoForm, self.stimStr))
        if self.expSettings.logFP != None:
            self.expSettings.logFP.flush()


    def nextDay (self, mice):
        for mouse in mice.generator():
            mouse.stimResultsDict.update ({'HFrewards' : 0})
            mouse.updateStats (self.expSettings.statsFP)


    def tester(self):
        """
        Tester function to be called from the hardwareTester
        makes a sample mouse and calls the run function in a loop, giving option to change settings every time
        """
        self.configStim (Mouse (2525, 0,0,0,{}))
        print ('Testing with dummy mouse:')
        self.mouse.show()
        CAD.Show_ordered_dict (self.expSettings.stimDict, 'Settings for LEDs Stimulator')
        while True:
            response = input ('change stimulus settings (yes or no)?')
            if response [0] == 'Y' or response [0] == 'y':
                CAD.Edit_dict (self.expSettings.stimDict, 'LEDs Stimulator')
                self.setup ()
            response = input ('run stimulator as configured (yes or no)?')
            if response [0] == 'Y' or response [0] == 'y':
                self.run ()
                self.logfile()
                self.mouse.show()
            else:
                break

