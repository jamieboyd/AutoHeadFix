#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse
import RPi.GPIO as GPIO
from time import time, sleep
from datetime import datetime
from random import random

class AHF_Stimulator_LEDs (AHF_Stimulator):

    @staticmethod
    def dict_from_user (stimDict):
        if not 'left_led_pin' in stimDict:
            stimDict.update ({'left_led_pin' : 18})
        if not 'center_led_pin' in stimDict:
            stimDict.update ({'center_led_pin' : 18})
        if not 'right_led_pin' in stimDict:
            stimDict.update ({'right_led_pin' : 18})
        if not 'led_on_time' in stimDict:
            stimDict.update ({'led_on_time' : 5e-03})
        if not 'led_off_time' in stimDict:
            stimDict.update ({'led_off_time' : 5e-03})
        if not 'train_time' in stimDict:
            stimDict.update ({'train_time' : 0.5})
        return super(AHF_Stimulator_LEDs, AHF_Stimulator_LEDs).dict_from_user (stimDict)

    def setup (self):
        super().setup()
        # 3 leds - left, right, center, controlled by 3 GPIO pins as indicated
        self.left_led_pin = int(self.configDict.get ('left_led_pin', 18))
        self.center_led_pin = int(self.configDict.get ('center_led_pin', 18))
        self.right_led_pin =  int(self.configDict.get ('right_led_pin', 18))
        # ON and OFF times for each pulse, and duration of each train
        self.led_on_time =  float(self.configDict.get ('led_on_time', 5e-03))
        self.led_off_time = float (self.configDict.get ('led_off_time', 5e-03))
        self.train_time = float(self.configDict.get ('train_time', 0.2))
        self.pulseTime = self.led_on_time + self.led_off_time
        self.nFlashes = int(self.train_time/self.pulseTime)
        # setup gpio for leds
        GPIO.setup (self.left_led_pin, GPIO.OUT, initial = GPIO.LOW)
        GPIO.setup (self.center_led_pin, GPIO.OUT, initial = GPIO.LOW)
        GPIO.setup (self.right_led_pin, GPIO.OUT, initial = GPIO.LOW)
        # calculate wait times
        self.waitTime1 = float((self.rewardInterval/2) - self.rewarder.rewardDict.get ('task'))
        self.waitTime2 = float((self.rewardInterval/2) - self.train_time)
        # calculate stim times
        self.flashOnArray = []
        self.flashOffArray=[]
        for iFlash in range (self.nFlashes):
            self.flashOnArray.append (self.led_on_time + (iFlash * self.pulseTime))
            self.flashOffArray.append ((iFlash + 1) * self.pulseTime)
        # update  config dict
        self.configDict.update ({'left_led_pin' : self.left_led_pin, 'center_led_pin' : self.center_led_pin, 'right_led_pin' : self.right_led_pin})
        self.configDict.update ({'led_on_time' : self.led_on_time, 'led_off_time' : self.led_off_time , 'train_time' : self.train_time})

    def configStim (self, mouse):
        self.stimStr = super().configStim (mouse)
        if not 'LCR' in mouse.stimResultsDict:
            mouse.stimResultsDict.update ({'LCR' : [0,0,0]})
        stimArray = mouse.stimResultsDict.get('LCR')
        ranVal = random ()
        if ranVal < 0.3333:
            self.stimPin = self.left_led_pin
            self.stimStr += ' L'
            stimArray [0] += self.nRewards
        elif ranVal < 0.6666:
            self.stimPin = self.center_led_pin
            self.stimStr += ' C'
            stimArray [1] += self.nRewards
        else:
            self.stimPin = self.right_led_pin
            self.stimStr += ' R'
            stimArray [2] += self.nRewards
        return self.stimStr


    def run(self):
        self.rewardTimes = []
        self.stimTimes = []
        fudge = 0.25e-03 # offset time added to array, so first pulse is same length as following pulses
        sleepMin = 1e-03 # mimimum time to call a sleep before looping
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(self.waitTime1)
            offset = time() + fudge
            onArray = [x + offset for x in self.flashOnArray]
            offArray = [x + offset for x in self.flashOffArray]
            for iFlash in range (self.nFlashes):
                GPIO.output(self.stimPin, GPIO.HIGH)
                sleepTime = onArray[iFlash] - time() - sleepMin
                if (sleepTime > 0):
                    sleep (sleepTime)
                while time() < onArray[iFlash]:
                    pass
                GPIO.output(self.stimPin, GPIO.LOW)
                sleepTime = offArray[iFlash] - time() - sleepMin
                if (sleepTime > 0):
                    sleep (sleepTime)
                while time() < offArray[iFlash]:
                    pass
            self.stimTimes.append (offset)
            sleep(self.waitTime2)
        self.mouse.headFixRewards += self.nRewards


    def logfile(self):
        mStr = '{:013}'.format(self.mouse.tag) + '\t'
        for rewardTime, stimTime in zip (self.rewardTimes,self.stimTimes):
            event = 'reward'
            outPutStr = mStr  + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + '\t' + event
            print (outPutStr)
            if self.textfp != None:
                outPutStr = mStr +  '{:.2f}'.format (rewardTime) + '\t'  + event
                self.textfp.write(outPutStr + '\n')
                self.textfp.flush()
            event = self.stimStr
            outPutStr = mStr + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + '\t' + event
            print (outPutStr)
            if self.textfp != None:
                outPutStr = mStr + '{:.2f}'.format (rewardTime) + '\t'  + event
                self.textfp.write(outPutStr + '\n')
                self.textfp.flush()


    def change_config (self, changesDict):
        super().change_config (changesDict)
        self.setup ()


    def config_from_user (self):
        super().config_from_user ()
        self.setup ()

if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        GPIO.setmode(GPIO.BCM)
        rewarder = AHF_Rewarder (30e-03, 24)
        rewarder.addToDict ('task', 50e-03)
        thisMouse = Mouse (2525, 0,0,0,0)
        #stimdict = AHF_Stimulator_LEDs.dict_from_user({})
        stimdict = {'nRewards' : 5, 'rewardInterval' : 1.5, 'left_led_pin' : 18, 'center_led_pin' : 18, 'right_led_pin' : 18}
        stimdict.update ({'led_on_time' : 0.5e-03, 'led_off_time' : 0.5e-03, 'train_time' : 0.5})
        stimulator = AHF_Stimulator_LEDs (stimdict, rewarder, None)
        stimulator.configStim (thisMouse)
        stimulator.run ()
        stimulator.logfile()
        stimulator.config_from_user()
        stimulator.configStim (thisMouse)
        stimulator.run ()
        stimulator.logfile()
        thisMouse.show()
    except Exception as er:
        print ('Error:' + str (er))
    finally:
        GPIO.cleanup ()
