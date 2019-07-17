#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_CageSet import AHF_CageSet
import RPi.GPIO as GPIO
from time import sleep
import RFIDTagReader
from AHF_HeadFixer import AHF_HeadFixer
from AHF_Rewarder import AHF_Rewarder
from AHF_Stimulator import AHF_Stimulator
from AHF_Mouse import Mouse, Mice
from time import time


def hardwareTester (cageSet, expSettings, tagReader, headFixer, rewarder, lickDetector, stimulator, mice):
    """
    Presents a menu asking user to choose a bit of hardware to test, and runs the tests

    If a test fails, a dialog is presented asking user to change the pin setup. The modified pinout
    can be saved, overwriting the configuration in ./AHF_Config.jsn
    Commands are:
    t= tagReader: trys to read a tag and, if successful, monitors Tag in Range Pin until tag goes away
    r = reward solenoid:  Opens the reward solenoid for a 1 second duration, then closes it
    c = contact check:  Monitors the head contact pin until contact, and then while contact is maintained
    f = head Fixer: runs tester function from head fixer class
    l = LED: Turns on the brain illumination LED for a 2 second duration, then off
    k = licK detector
    s = stimulator : runs tester function from stimulator class
    h = sHow config settings: Prints out the current pinout in the AHF_CageSet object
    v = saVe modified config file: Saves the the AHF_CageSet object to the file ./AHF_config.jsn
    q = quit: quits the program
    """
    queryStr = '\nt=tagReader, r=reward solenoid, c=contact check, f=head Fixer, l=LED, '
    if lickDetector is not None:
        queryStr +=  'k=licK detector, '
    queryStr += 's=stimulator tester, h=sHow config settings, v=saVe modified config file, q=Quit Hardware Tester: '
    try:
        while (True):
            inputStr = input (queryStr)
            # ***************************** t for tag reader **********************************
            if inputStr == 't':
                print ('Monitoring tag reader for next 10 seconds')  
                endTime = time() + 10
                nEntry =0
                nExit =0
                thisTag = RFIDTagReader.globalTag
                while time () < endTime:
                    if RFIDTagReader.globalTag != thisTag:
                        if RFIDTagReader.globalTag == 0:
                            print ('Tag {:013d} just went away'.format (thisTag))
                            nExit +=1
                        else:
                            print ('Tag {:013d} just entered'.format (RFIDTagReader.globalTag))
                            nEntry += 1
                        thisTag = RFIDTagReader.globalTag
                    #sleep (0.05)
                if nEntry < 2 or nExit < 2:
                    inputStr = input ('Only {:d} entries and {:d} exits. Do you want to change the tag-in-range Pin (currently {:d})?'.format (nEntry, nExit, cageSet.tirPin))
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        tagReader.removeCallback ()
                        cageSet.tirPin = int (input('Enter New tag-in-range Pin:'))
                        tagReader.installCallback (cageSet.tirPin)
            # ***************************** # k for licK detector **********************************
            elif inputStr == 'k': 
                lickDetector.test (cageSet)
            # ***************************** # r for reward solenoid **********************************
            elif inputStr == 'r': 
                rewarder.addToDict('test', 1.0)
                print ('Reward Solenoid opening for 1 sec')
                rewarder.giveReward ('test')
                sleep(1.0)
                inputStr= input('Do you want to change the Reward Solenoid Pin (currently {:d})?'.format(rewarder.rewardPin))
                if inputStr[0] == 'y' or inputStr[0] == "Y":
                    GPIO.cleanup (rewarder.rewardPin)
                    cageSet.rewardPin = int (input('Enter New Reward Solenoid Pin:' ))
                    rewarder.rewardPin = cageSet.rewardPin
                    GPIO.setup (cageSet.rewardPin, GPIO.OUT, initial=GPIO.LOW)
            # ***************************** #c for contact for head fix **********************************
            elif inputStr == 'c':
                err = False
                if GPIO.input (cageSet.contactPin)== expSettings.contactState:
                    print ('Contact pin already indicates contact.')
                    err=True
                else:
                    GPIO.wait_for_edge (cageSet.contactPin, expSettings.contactEdge, timeout= 10000)
                    if GPIO.input (cageSet.contactPin)== expSettings.noContactState:
                        print ('No Contact after 10 seconds.')
                        err = True
                    else:
                        print ('Contact Made.')
                        GPIO.wait_for_edge (cageSet.contactPin, expSettings.noContactEdge, timeout= 10000)
                        if GPIO.input (cageSet.contactPin)== expSettings.contactState:
                            print ('Contact maintained for 10 seconds.')
                            err = True
                        else:
                            print ('Contact Broken')
                if err:
                    inputStr= input ('Do you want to change Contact settings (currently pin={:d}, polarity={:s}, pull up/down = {:s})?'.format(cageSet.contactPin, cageSet.contactPolarity, cageSet.contactPUD))
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        cageSet.contactPin= int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:'))
                        contactInt = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
                        if contactInt == 0:
                            cageSet.contactPolarity = 'FALLING'
                        else:
                            cageSet.contactPolarity = 'RISING'
                        contactInt = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
                        if contactInt ==0:
                            cageSet.contactPUD = 'OFF'
                        elif contactInt == 1:
                            cageSet.contactPUD = 'DOWN'
                        else:
                            cageSet.contactPUD='UP'
                        GPIO.setup (cageSet.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + cageSet.contactPUD))
                        if cageSet.contactPolarity =='RISING':
                            expSettings.contactEdge = GPIO.RISING
                            expSettings.noContactEdge = GPIO.FALLING
                            expSettings.contactState = GPIO.HIGH
                            expSettings.noContactState = GPIO.LOW
                        else:
                            expSettings.contactEdge = GPIO.FALLING
                            expSettings.noContactEdge = GPIO.RISING
                            expSettings.contactState = GPIO.LOW
                            expSettings.noContactState = GPIO.HIGH
            # ***************************** # f for head Fixer, run test from headFixer class **********************************
            elif inputStr == 'f': 
                headFixer.test(cageSet)
             # ***************************** # l for LED trigger **********************************
            elif inputStr == 'l': 
                print ('LED turning ON for 2 seconds.')
                GPIO.output(cageSet.ledPin, 1)
                sleep (2)
                GPIO.output(cageSet.ledPin, 0)
                inputStr=input ('LED turned OFF\nDo you want to change the LED Pin (currently {:d})?'.format(cageSet.ledPin))
                if inputStr == 'y' or inputStr == "Y":
                    GPIO.cleanup (cageSet.ledPin)
                    cageSet.ledPin = int (input('Enter New LED Pin:'))
                    GPIO.setup (cageSet.ledPin, GPIO.OUT, initial = GPIO.LOW)
            # ***************************** # s for stimulator, run test from stimlator class **********************************
            elif inputStr == 's':
                stimulator.tester (mice)
            # ***************************** # h for sHow prints settings to the shell **********************************
            elif inputStr == 'h':
                cageSet.show()
            # ***************************** # v for saVe saves settings to congig jsn file **********************************
            elif inputStr=='v':
                cageSet.save()
            # ***************************** q for quit. quits hardware tester function/program ********************************
            elif inputStr == 'q':
                break
    except KeyboardInterrupt:
        print ("harware tester quitting.")

            
if __name__ == '__main__':
    
    class simpleExpSetings (object):
        """
        Some info about contact edges is translated from the cageSet and saved in the experiment settings, so we spoof that
        here to use the same test code for contact check when run form main as when run from the hardware tester option in the main program
        we also add a stimulator - the only testable object in exp setings 
        """
        def __init__(self, cageSettings):
            self.stimulator = 'Rewards'
            self.stimDict = {'nRewards' : 5, 'rewardInterval' : 2}
            self.settingsDict = {'stimulator' : self.stimulator, 'stimParams' : self.stimDict}
            self.logFP = None
            if cageSettings.contactPolarity == 'RISING':
                self.contactEdge = GPIO.RISING
                self.noContactEdge = GPIO.FALLING
                self.contactState = GPIO.HIGH
                self.noContactState = GPIO.LOW
            else:
                self.contactEdge = GPIO.FALLING
                self.noContactEdge = GPIO.RISING
                self.contactState = GPIO.LOW
                self.noContactState = GPIO.HIGH
                
    def hardwareTester_for_main ():
        """
        When run as main, hardware Tester allows you to verify the various hardware bits are working, also test stimulator
        without running full Auto Head Fixing program. Initialize hardware, then runs the regular hardware tester function
        """
        cageSet = AHF_CageSet() # loads cage settings from AHF_config.jsn
        expSettings = simpleExpSetings (cageSet) # exp settings contains contact edge and state, plus stimulator
        GPIO.setmode (GPIO.BCM) # set up GPIO to use BCM mode for GPIO pin numbering
        GPIO.setwarnings(False) # supresses warnings for using previously configured pins
        GPIO.setup (cageSet.ledPin, GPIO.OUT) # LED for brain illumination, one simpe GPIO pin for output
        rewarder = AHF_Rewarder (30e-03, cageSet.rewardPin) # make rewarder and add a test reward
        GPIO.setup (cageSet.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + cageSet.contactPUD)) # contact check pin can have a pullup/down resistor
        headFixer=AHF_HeadFixer.get_class (cageSet.headFixer) (cageSet) # initialize headFixer
        
        tagReader = RFIDTagReader.TagReader(cageSet.serialPort, True, timeOutSecs = 0.05, kind = 'ID') # initialize tagReader
        tagReader.installCallback (cageSet.tirPin)
        
        if cageSet.lickIRQ == 0:  # start lick detector, if one is installed
            lickDetector = None
        else:
            from AHF_LickDetector import AHF_LickDetector
            lickDetector = AHF_LickDetector (cageSet.lickChans, cageSet.lickIRQ, None)
        stimulator = AHF_Stimulator.get_class (expSettings.stimulator) (cageSet, expSettings, rewarder, lickDetector)
        stimDict = expSettings.stimDict
        hardwareTester (cageSet, expSettings, tagReader, headFixer, rewarder, lickDetector, stimulator, Mice())
        GPIO.cleanup() # this ensures a clean exit


    hardwareTester_for_main ()
    


