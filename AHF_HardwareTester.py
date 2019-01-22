#! /usr/bin/python3
#-*-coding: utf-8 -*-

import AHF_ClassAndDictUtils
from AHF_Task import Task
from AHF_HeadFixer import AHF_HeadFixer
from AHF_Stimulator import AHF_Stimulator
from AHF_Rewarder import AHF_Rewarder
from AHF_Camera import AHF_Camera
from AHF_TagReader import AHF_TagReader
import RPi.GPIO as GPIO
from time import sleep, time


if __name__ == '__main__':
    def hardwareTester ():
        """
        Hardware Tester for Auto Head Fixing, allows you to verify the various hardware bits are working
        Single GPIO pin stuff: pin numbers and possibly polarities etc. stored in config:
        Brain Illumination LED, Contact Check, entry Beam Break
        Objects: created from info in config, pointer to them stored in task
        tagReader, headFixer, rewarder, stimulator, lick detetctor
        """
        # when run as __main__, user chooses exp config file
        task = Task('')
        # set up GPIO to use BCM mode for GPIO pin numbering
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        # set up pin that turns on brain illumination LED
        GPIO.setup (task.ledPin, GPIO.OUT, initial = GPIO.LOW)
        # initialize rewarder
        rewarder = AHF_ClassAndDictUtils.Class_from_file('Rewarder', task.RewarderClass) (task.RewarderDict)
        #Class_from_file(nameTypeStr, nameStr)
        #AHF_Rewarder.get_class (task.RewarderName) (task)
        
        # set up pin for ascertaining mouse contact, ready for head fixing
        GPIO.setup (task.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + task.contactPUD))
        # set up entry beam break pin, if we have it
        if task.hasEntryBeamBreak:
            GPIO.setup (task.entryBBpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        setattr (task, 'rewarder', rewarder)
        # initialize head fixer object
        headFixer=AHF_HeadFixer.get_class (task.headFixerName) (task)
        setattr (task, 'headFixer', headFixer)
        # initialize TagReader
        #tagReader = 
        try:
            tagReader = RFIDTagReader.TagReader (task.serialPort, True,timeOutSecs = None, kind='ID')
            tagReader.installCallBack (task.tirPin)
        except IOError:
            tagReader = None
        setattr (task, 'tagReader', tagReader)
        # initialize lick detetctor
        if task.hasLickDetector:
            import AHF_LickDetector
            lickDetector = AHF_LickDetector.LickDetector (task.lickIRQ, None)
            setattr (task, 'lickDetector', lickDetector)
        # now that hardware is initialized, enter hardware test loop
        htloop (task)
        # now test a few things, make sure changes were applied
        print ('checking...')
        print ('headFixer fixed pos = ', task.headFixer.servoFixedPosition, 'released position = ',task.headFixer.servoReleasedPosition) 
else:
    def hardwareTester (task):
        """
        Hardware Tester for Auto Head Fixing, allows you to verify the various hardware bits are working
        """
        htloop (task)

def htloop (task):
    """
    Presents a menu asking user to choose a bit of hardware to test, and runs the tests

    If a test fails, a dialog is presented asking user to change the pin setup. The modified pinout
    can be saved, overwriting the configuration in ./AHF_Config.jsn
    Commands are:
    t= TagReader: trys to read a tag and, if successful, monitors Tag in Range Pin until tag goes away
    r = Reward solenoid:  Opens the reward solenoid for a 1 second duration, then closes it
    c = Contact check:  Monitors the head contact pin until contact, and then while contact is maintained
    f = head Fixer: runs test function from loaded head fixer class
    s = Stimulator: runs test function from loaded stmulator class
    e = Entry beam break
    l = LED: Turns on the brain illumination LED for a 2 second duration, then off
    k = licK detector: verified licks are being registered
    a = camerA: check and verify settings for camera
    h = sHow config settings: Prints out the current pinout in the AHF_task object
    v = saVe modified config file: Saves the the AHF_task object to the file ./AHF_Config.jsn
    q = quit: quits the program
    """

    try:
        menuStr = '\n---------Hardware tester---------\nt = tagReader\nr = reward solenoid\nc = contact check'
        if task.hasEntryBeamBreak:
            menuStr += '\ne = entry beam break'
        menuStr += '\nf = head Fixer\ns = Stimulator\nl = LED'
        if task.hasLickDetector:
            menuStr += '\nk = licK detector'
        menuStr += '\nh=sHow config\nv= saVe config\nq=quit:'
        while (True):
            inputStr = input (menuStr)
            if inputStr == 't': # t for tagreader
                print ('\nWaiting for a tag....')
                startTime = time()
                tagReaderError = False
                try:
                    while RFIDTagReader.globalTag == 0 and time () < startTime + 10:
                        sleep (0.05)
                    if time () > startTime + 10:
                        print ('No tag read in 10 seconds.')
                        tagReaderError = True
                    else:
                        print ('Read a tag ', RFIDTagReader.globalTag)
                        startTime = time()
                        while RFIDTagReader.globalTag != 0 and time () < startTime + 10:
                            sleep (0.33)
                            print ('Tag is still in range')
                        if time () > startTime + 10:
                            print ('Tag is still in range after 10 seconds.')
                            tagReaderError = True
                        else:
                            print ('Tag is no longer in range')
                except IOError as anError:
                    tagReaderError = True
                    print ('Tag Reader not set up properly:' + str (anError))
                if tagReaderError > 0:
                    inputStr= input('Do you want to change the tag reader port (currently ' + str (task.serialPort) + ') or tag-in-range pin (currently ' + str (task.tirPin) + ')?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        task.serialPort = input ('Enter New Serial Port:')
                        task.tirPin = int (input('Enter New tag-in-range Pin:'))
                        task.tagReader = RFIDTagReader.TagReader (task.serialPort, True,timeOutSecs = None, kind='ID')
                        task.tagReader.installCallBack (task.tirPin)
            elif inputStr == 'r': # r for reward solenoid
                rewarder.hardwareTest()
            elif inputStr == 'c': #c for contact on head fix
                err = False
                if task.contactPolarity == 'RISING':
                    contactEdge = GPIO.RISING 
                    noContactEdge = GPIO.FALLING
                    contactState = GPIO.HIGH
                    noContactState = GPIO.LOW
                else:
                    contactEdge = GPIO.FALLING
                    noContactEdge = GPIO.RISING
                    contactState = GPIO.LOW
                    noContactState = GPIO.HIGH
                if GPIO.input (task.contactPin)== contactState:
                    print ('\nContact pin already indicates contact.')
                    err=True
                else:
                    print ('\nWaiting for Contact....')
                    channel = GPIO.wait_for_edge (task.contactPin, contactEdge, timeout=10000)
                    if channel is None:
                        print ('No Contact made after 10 seconds.')
                        err = True
                    else:
                        print ('Contact Made.')
                        channel = GPIO.wait_for_edge (task.contactPin, noContactEdge, timeout=10000)
                        if channel is None:
                            print ('Contact maintained for longer than 10 seconds.')
                            err = True
                        else:
                            print ('Contact Broken')
                            err = False
                if err:
                    inputStr= input ('Do you want to change Contact settings (currently pin=' + str (task.contactPin) + ', polarity=' + str(task.contactPolarity) + ', pull up/down =' + str (task.contactPUD) + ')?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        task.contactPin= int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:'))
                        contactInt = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
                        if contactInt == 0:
                            task.contactPolarity = 'FALLING'
                        else:
                            task.contactPolarity = 'RISING'
                        contactInt = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
                        if contactInt ==0:
                            task.contactPUD = 'OFF'
                        elif contactInt == 1:
                            task.contactPUD = 'DOWN'
                        else:
                            task.contactPUD='UP'
                    GPIO.setup (task.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + task.contactPUD))
            elif inputStr == 'e': # beam break at enty
                err = False
                if GPIO.input (task.entryBBpin)== GPIO.LOW:
                    print ('\nEntry beam break is already broken')
                    err=True
                else:
                    print ('\nWaiting for Beam Break....')
                    GPIO.wait_for_edge (task.entryBBpin, GPIO.FALLING, timeout= 10000)
                    if GPIO.input (task.entryBBpin)== GPIO.HIGH:
                        print ('Entry beam not broken after 10 seconds.')
                        err = True
                    else:
                        print ('Entry Beam Broken.')
                        GPIO.wait_for_edge (task.entryBBpin, GPIO.RISING, timeout= 10000)
                        if GPIO.input (task.entryBBpin)== GPIO.LOW:
                            print ('Entry Beam Broken maintained for longer than 10 seconds.')
                            err = True
                        else:
                            print ('Entry Beam Intact Again.')
                            err = False
                if err:
                    inputStr= input ('Do you want to change the Entry Beam Break Pin (currently pin=' + str (task.entryBBpin)+ '?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        task.entryBBpin= int (input ('Enter the GPIO pin connected to the tube entry IR beam-breaker:'))
                        GPIO.setup (task.entryBBpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            elif inputStr == 'f': # head Fixer, run test from headFixer class
                task.headFixer.test(task)
            elif inputStr == 'k': # licK detretctor, run tests from lick detetor
                task.lickDetector.test (task)
            elif inputStr == 's':
                stimClass = AHF_ClassAndDictUtils.Class_from_file(task.StimulatorClass)
                stimclass.hardwareTest (task)
            elif inputStr == 'l': # l for LED trigger
                print ('\nLED turning ON for 2 seconds.')
                GPIO.output(task.ledPin, 1)
                sleep (2)
                GPIO.output(task.ledPin, 0)
                inputStr=input ('LED turned OFF\nDo you want to change the LED Pin (currently ' + str(task.ledPin) + ')?')
                if inputStr == 'y' or inputStr == "Y":
                    task.ledPin = int (input('Enter New LED Pin:'))
                    GPIO.setup (task.ledPin, GPIO.OUT, initial = GPIO.LOW)
            elif inputStr == 'h':
                task.show()
            elif inputStr=='v':
                task.save()
            elif inputStr == 'q':
                break
    except KeyboardInterrupt:
        print ("quitting.")
    finally:
        if __name__ == '__main__':
            GPIO.cleanup() # this ensures a clean exit

if __name__ == '__main__':
    hardwareTester()
