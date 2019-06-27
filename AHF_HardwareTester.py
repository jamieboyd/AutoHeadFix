#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_CageSet import AHF_CageSet
import RPi.GPIO as GPIO
from time import sleep

from RFIDTagReader import TagReader
from AHF_HeadFixer import AHF_HeadFixer
from AHF_Rewarder import AHF_Rewarder
from time import time


def hardwareTester (cageSet, expSettings, tagReader, headFixer, rewarder, lickDetector, stimulator, stimDict):
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
    l = LED: Turns on the brain illumination LED for a 2 second duration, then off
    s = stimulator tester
    h = sHow config settings: Prints out the current pinout in the AHF_CageSet object
    v = saVe modified config file: Saves the the AHF_CageSet object to the file ./AHF_config.jsn
    q = quit: quits the program
    """
    try:
        while (True):
            inputStr = input ('t=tagReader, r=reward solenoid, c=contact check, f=head Fixer, l=LED, s=stimulator tester, h=sHow config, v= saVe config, q=quit:')
            if inputStr == 't': # t for tagreader
                if tagReader is None:
                    cageSet.serialPort = input ('First, set the tag reader serial port, likely /dev/serial0 or dev/ttyUSB0:')
                    try:
                        tagReader = TagReader (cageSet.serialPort, True)
                    except IOError as anError:
                        print ('Tag reader not found at {:s}. Try setting the serial port again.'.format(cageSet.serialPort))
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
                    GPIO.wait_for_edge (cageSet.contactPin, contactEdge, timeout= 10000)
                    if GPIO.input (cageSet.contactPin)== noContactState:
                        print ('No Contact after 10 seconds.')
                        err = True
                    else:
                        print ('Contact Made.')
                        GPIO.wait_for_edge (cageSet.contactPin, noContactEdge, timeout= 10000)
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
            elif inputStr == 'h':
                cageSet.show()
            elif inputStr=='v':
                cageSet.save()
            elif inputStr == 'q':
                break
    except KeyboardInterrupt:
        print ("harware tester quitting.")

            
if __name__ == '__main__':
    
    class simpleExpSetings (AHF_Settings):
        """
        Some info about contact edges is translated from the cageSet and saved in the experiment settings, so we spoof that
        here to use the same test code for contact check when run form main as when run from the hardware tester optionin the main program
        """
        def __init__(self, cageSettings):
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
        expSettings = simpleExpSetings (cageSet) # exp settings contains contact edge and state, simpleExpSetings does just that and no more

        GPIO.setmode (GPIO.BCM) # set up GPIO to use BCM mode for GPIO pin numbering
        GPIO.setwarnings(False) # supresses warnings for using previously configured pins

        GPIO.setup (cageSet.ledPin, GPIO.OUT) # LED for brain illumination, one simpe GPIO pin for output

        rewarder = AHF_Rewarder (30e-03, cageSet.rewardPin) # make rewarder and add a test reward
        rewarder.addToDict('test', 1.0)
        
        GPIO.setup (cageSet.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + cageSet.contactPUD)) # contact check pin can have a pullup/down resistor

        
        # make RFID reader and install callback
        try:
            tagReader = TagReader(cageSet.serialPort, True, timeOutSecs = 50e-03)
            tagReader.installCallback (cageSet.tirPin)
        except Exception as e:
            tagReader = None
        
        # initialize head fixer
        try:
            headFixer=AHF_HeadFixer.get_class (cageSet.headFixer) (cageSet)
        except Exception as e:
            headFixer = None
            

        # start lick detector, if one is installed
        if cageSet.lickIRQ == 0:
            lickDetector = None
        else:
            from AHF_LickDetector import AHF_LickDetector, Simple_Logger
            try:
                lickDetector = AHF_LickDetector (cageSet.lickChans, cageSet.lickIRQ, Simple_Logger (None))
            except IOError:
                lickDetector = None
                
        hardwareTester (cageSet, expSettings, tagReader, headFixer, rewarder, lickDetector, stimulator, stimDict)
        GPIO.cleanup() # this ensures a clean exit


    hardwareTester_for_main ()
    


