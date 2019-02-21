#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse

from time import time, localtime,timezone, sleep
from datetime import datetime

#RPi module
import RPi.GPIO as GPIO

class AHF_Stimulator_Rewards (AHF_Stimulator):
    
    def __init__ (self, cageSettings, expSettings, rewarder, lickDetector, camera):
        super().__init__(cageSettings, expSettings, rewarder, lickDetector, camera)
        self.setup()

    def setup (self):
        self.nRewards = int (self.configDict.get('nRewards', 2))
        self.rewardInterval = float (self.configDict.get ('rewardInterval', 2))
        self.configDict.update({'nRewards' : self.nRewards, 'rewardInterval' : self.rewardInterval})


    @staticmethod
    def dict_from_user (stimDict):
        if not 'nRewards' in stimDict:
            stimDict.update ({'nRewards' : 5})
        if not 'rewardInterval' in stimDict:
            stimDict.update ({'rewardInterval' : 5.0})
        return super(AHF_Stimulator_Rewards, AHF_Stimulator_Rewards).dict_from_user (stimDict)
        
    def run(self):
        
        #================ Debug ====================
        sleep(0.3)
        ref_path = self.cageSettings.dataPath+'sample_im/'+datetime.fromtimestamp (int (time())).isoformat ('-')+'_'+str(self.mouse.tag)+'.jpg'
        self.camera.capture(ref_path)
        self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
        
        timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
        self.rewardTimes = []
        for reward in range(self.nRewards):
            self.rewardTimes.append (time())
            self.rewarder.giveReward('task')
            sleep(timeInterval)
        self.mouse.headFixRewards += self.nRewards

        self.camera.stop_preview()

    def inspect_mice(self,mice,cageSettings,expSettings):
        #Inspect the mice array
        print('MouseID\t\theadFixStyle\tstimType\tgenotype')
        for mouse in mice.mouseArray:
            headFixStyle = 'fix'
            if mouse.headFixStyle == 1:
                headFixStyle = 'loose'
            elif mouse.headFixStyle == 2:
                headFixStyle = 'nofix'
            if hasattr(mouse, 'genotype'):
                genotype = expSettings.genotype[mouse.genotype]
            else:
                genotype = 'no genotype'
            stimType = expSettings.stimulator[mouse.stimType][15:22]
            print(str(mouse.tag)+'\t'+headFixStyle + '\t\t' + stimType + '\t\t' + genotype)
        while(True):
            inputStr = input ('c= headFixStyle, s= stimType, q= quit: ')
            if inputStr == 'c':
                while(True):
                    inputStr =  int(input ('Type the tagID of mouse to change headFixStyle:'))
                    for mouse in mice.mouseArray:
                        if mouse.tag == inputStr:
                            inputStr = int(input('Change headFixStyle to:\n0: fix\n1: loose\n2: nofix\n'))
                            if inputStr == 0:
                                mouse.headFixStyle = 0
                            elif inputStr == 1:
                                mouse.headFixStyle = 1
                            elif inputStr == 2:
                                mouse.headFixStyle = 2

                    inputStr = input('Change value of another mouse?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        continue
                    else:
                        break

            elif inputStr == 's':
                while(True):
                    inputStr =  int(input ('Type the tagID of mouse to change stimType:'))
                    for mouse in mice.mouseArray:
                        if mouse.tag == inputStr:
                            print('Following stimTypes are available:')
                            for i,j in enumerate(expSettings.stimulator):
                                print(str(i)+': '+j[15:])
                            inputStr = int(input('Change stimType to:'))
                            mouse.stimType = inputStr

                    inputStr = input('Change value of another mouse?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        continue
                    else:
                        break
                    
            elif inputStr == 'q':
                break

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
        
    def logfile (self):
        event = 'reward'
        mStr = '{:013}'.format(self.mouse.tag)
        for rewardTime in self.rewardTimes:
            outPutStr = mStr + '\t' + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') + '\t' + event
            print (outPutStr)
        if self.textfp != None:
            for rewardTime in self.rewardTimes:
                outPutStr = mStr + '\t' + '{:.2f}'.format (rewardTime) + '\t'  + event +  "\t"  + datetime.fromtimestamp (int (rewardTime)).isoformat (' ') 
                self.textfp.write(outPutStr + '\n')
            self.textfp.flush()



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
    

    
