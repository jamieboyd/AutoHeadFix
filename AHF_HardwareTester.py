#! /usr/bin/python3
#-*-coding: utf-8 -*-


import RPi.GPIO as GPIO
from time import sleep
from RFIDTagReader import TagReader
from AHF_HeadFixer import AHF_HeadFixer
from AHF_CageSet import AHF_CageSet
from time import time

if __name__ == '__main__':
    def hardwareTester ():
        """
        Hardware Tester for Auto Head Fixing, allows you to verify the various hardware bits are working
        """
        cageSet = AHF_CageSet()
        # set up GPIO to use BCM mode for GPIO pin numbering
        GPIO.setwarnings(False)
        GPIO.setmode (GPIO.BCM)
        GPIO.setup (cageSet.rewardPin, GPIO.OUT)
        GPIO.setup (cageSet.ledPin, GPIO.OUT)
        GPIO.setup (cageSet.tirPin, GPIO.IN)
        if cageSet.hasEntryBB:
            GPIO.setup (cageSet.entryBBpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # contact pin can have a pullup/down resistor enabled
        GPIO.setup (cageSet.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + cageSet.contactPUD))
        # initialize head fixer
        headFixer=AHF_HeadFixer.get_class (cageSet.headFixer) (cageSet)
        # open TagReader
        try:
            tagReader = AHF_TagReader (cageSet.serialPort, True)
        except IOError:
            tagReader = None
        htloop (cageSet, tagReader, headFixer, stimulator, expSettings)
else:
    def hardwareTester (cageSet, tagReader, headFixer, stimulator, expSettings):
        """
        Hardware Tester for Auto Head Fixing, allows you to verify the various hardware bits are working
        """
        htloop (cageSet, tagReader, headFixer, stimulator, expSettings)


def htloop (cageSet, tagReader, headFixer, stimulator, expSettings):
    """
    Presents a menu asking user to choose a bit of hardware to test, and runs the tests

    If a test fails, a dialog is presented asking user to change the pin setup. The modified pinout
    can be saved, overwriting the configuration in ./AHF_Config.jsn
    Commands are:
    t= tagReader: trys to read a tag and, if successful, monitors Tag in Range Pin until tag goes away
    r = reward solenoid:  Opens the reward solenoid for a 1 second duration, then closes it
    c = contact check:  Monitors the head contact pin until contact, and then while contact is maintained
    f = head Fixer
    e = Entry beam break
    p = pistons solenoid: Energizes the pistons for a 2 second duration, and then de-energizes them
    l = LED: Turns on the brain illumination LED for a 2 second duration, then off
    h = sHow config settings: Prints out the current pinout in the AHF_CageSet object
    v = saVe modified config file: Saves the the AHF_CageSet object to the file ./AHF_Config.jsn
    q = quit: quits the program
    """
    if cageSet.contactPolarity == 'RISING':
          contactEdge = GPIO.RISING
          noContactEdge = GPIO.FALLING
          contactState = GPIO.HIGH
          noContactState = GPIO.LOW
    else:
          contactEdge = GPIO.FALLING
          noContactEdge = GPIO.RISING
          contactState = GPIO.LOW
          noContactState = GPIO.HIGH
    try:
        while (True):
            inputStr = input ('t=tagReader, r=reward solenoid, c=contact check, e= entry beam break, f=head Fixer, l=LED, s=stimulator tester, h=sHow config, v= saVe config, q=quit:')
            if inputStr == 't': # t for tagreader
                if tagReader == None:
                    cageSet.serialPort = input ('First, set the tag reader serial port:')
                    try:
                        tagReader = TagReader (cageSet.serialPort, True)
                        inputStr =  input ('Do you want to read a tag now?')
                        if inputStr[0] == 'n' or inputStr[0] == "N":
                            continue
                    except IOError as anError:
                        print ('Try setting the serial port again.')
                        tagReader = None
                if tagReader is not None:
                    try:
                        if (tagReader.serialPort.inWaiting() < 16):
                            print ('No data in serial buffer')
                            tagError = True
                        else:
                            tagID = tagReader.readTag()
                            tagError = False
                    except (IOError, ValueError) as anError:
                        tagError = True
                    if tagError == True:
                        print ('Serial Port Tag-Read Error\n')
                        tagReader.clearBuffer()
                        inputStr = input ('Do you want to change the tag reader serial port (currently ' + cageSet.serialPort + ')?')
                        if inputStr == 'y' or inputStr == "Y":
                            cageSet.serialPort = input ('Enter New Serial Port:')
                            # remake tagReader and open serial port
                            tagReader = TagReader (cageSet.serialPort, True)
                    else:
                        print ("Tag ID =", tagID)
                        # now check Tag-In-Range pin function
                        if (GPIO.input (cageSet.tirPin)== GPIO.LOW):
                            print ('Tag was never registered as being "in range"')
                            tagError = True
                        else:
                            startTime = time()
                            GPIO.wait_for_edge (cageSet.tirPin, GPIO.FALLING, timeout= 10000)
                            if (time () > startTime + 10.0):
                                print ('Tag stayed in range for over 10 seconds')
                                tagError = True
                            else:
                                print ('Tag no longer in range')
                                tagError = False
                        if (tagError == True):
                            inputStr = input ('Do you want to change the tag-in-range Pin (currently ' + str (cageSet.tirPin) + ')?')
                            if inputStr[0] == 'y' or inputStr[0] == "Y":
                                cageSet.tirPin = int (input('Enter New tag-in-range Pin:'))
                                GPIO.setup (cageSet.tirPin, GPIO.IN)
            elif inputStr == 'r': # r for reward solenoid
                print ('Reward Solenoid opening for 1 sec')
                GPIO.output(cageSet.rewardPin, 1)
                sleep(1.0)
                GPIO.output(cageSet.rewardPin, 0)
                inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin (currently ' + str (cageSet.rewardPin) + ')?')
                if inputStr[0] == 'y' or inputStr[0] == "Y":
                    cageSet.rewardPin = int (input('Enter New Reward Solenoid Pin:' ))
                    GPIO.setup (cageSet.rewardPin, GPIO.OUT, initial=GPIO.LOW)
            elif inputStr == 'c': #c for contact on head fix
                if GPIO.input (cageSet.contactPin)== contactState:
                    print ('Contact pin already indicates contact.')
                    err=True
                else:
                    GPIO.wait_for_edge (cageSet.contactPin, contactEdge, 100)
                    if GPIO.input (cageSet.contactPin)== noContactState:
                        print ('No Contact after 10 seconds.')
                        err = True
                    else:
                        print ('Contact Made.')
                        GPIO.wait_for_edge (cageSet.contactPin, noContactEdge, 100)
                        if GPIO.input (cageSet.contactPin)== contactState:
                            print ('Contact maintained for 10 seconds.')
                            err = True
                        else:
                            print ('Contact Broken')
                            err = False
                if err == True:
                    inputStr= input ('Do you want to change Contact settings (currently pin=' + str (cageSet.contactPin) + ', polarity=' + str(cageSet.contactPolarity) + ', pull up/down =' + str (cageSet.contactPUD) + ')?')
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
                        contactEdge = GPIO.RISING
                        noContactEdge = GPIO.FALLING
                        contactState = GPIO.HIGH
                        noContactState = GPIO.LOW
                    else:
                        contactEdge = GPIO.FALLING
                        noContactEdge = GPIO.RISING
                        contactState = GPIO.LOW
                        noContactState = GPIO.HIGH
            elif inputStr == 'e': # beam break at enty
                if GPIO.input (cageSet.entryBBpin)== GPIO.LOW:
                    print ('Entry beam break is already broken')
                    err=True
                else:
                    GPIO.wait_for_edge (cageSet.entryBBpin, GPIO.FALLING, timeout= 10000)
                    if GPIO.input (cageSet.entryBBpin)== GPIO.HIGH:
                        print ('Entry beam not broken after 10 seconds.')
                        err = True
                    else:
                        print ('Entry Beam Broken.')
                        GPIO.wait_for_edge (cageSet.entryBBpin, GPIO.RISING, timeout= 10000)
                        if GPIO.input (cageSet.entryBBpin)== GPIO.LOW:
                            print ('Entry Beam Broken maintained for 10 seconds.')
                            err = True
                        else:
                            print ('Entry Beam Intact Again.')
                            err = False
                if err == True:
                    inputStr= input ('Do you want to change the Entry Beam Break Pin (currently pin=' + str (cageSet.entryBBpin)+ '?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        cageSet.entryBBpin= int (input ('Enter the GPIO pin connected to the tube entry IR beam-breaker:'))
                        GPIO.setup (cageSet.entryBBpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            elif inputStr == 'f': # head Fixer, run test from headFixer class
                headFixer.test(cageSet)
            elif inputStr == 'l': # l for LED trigger
                print ('LED turning ON for 2 seconds.')
                GPIO.output(cageSet.ledPin, 1)
                sleep (2)
                GPIO.output(cageSet.ledPin, 0)
                inputStr=input ('LED turned OFF\nDo you want to change the LED Pin (currently ' + str(cageSet.ledPin) + ')?')
                if inputStr == 'y' or inputStr == "Y":
                    cageSet.ledPin = int (input('Enter New LED Pin:'))
                    GPIO.setup (cageSet.ledPin, GPIO.OUT, initial = GPIO.LOW)
            elif inputStr == 's':
                for i,j in enumerate(expSettings.stimulator):
                    print('\t'+str(i)+': '+str(j))
                inputStr = input ('Which stimulator tester would you like to run?')
                stimulator[int(inputStr)].tester(expSettings)
            elif inputStr == 'h':
                cageSet.show()
            elif inputStr=='v':
                cageSet.save()
            elif inputStr == 'q':
                break
    except KeyboardInterrupt:
        print ("quitting.")
    finally:
        if __name__ == '__main__':
            GPIO.cleanup() # this ensures a clean exit

if __name__ == '__main__':
    hardwareTester()
