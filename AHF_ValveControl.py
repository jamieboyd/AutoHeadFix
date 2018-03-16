#! /usr/bin/python
#-*-coding: utf-8 -*-


import RPi.GPIO as GPIO
from AHF_CageSet import AHF_CageSet

if __name__ == '__main__':
    def valveControl ():
        """
        Opens and closes valve, as for testing, or draining the lines

        When run as main, valveControl takes no paramaters and first loads/makes the AHF_CageSet instance
        and sets up GPIO. After setting up, valveControl runs in a loop with options 1 to open, 0 to close, q to quit the program
        """
        cageSet = AHF_CageSet()
        GPIO.setmode (GPIO.BCM)
        GPIO.setup (cageSet.rewardPin, GPIO.OUT, initial=GPIO.LOW)
        runLoop(cageSet)
else:
    def valveControl (cageSet):
        """
        Opens and closes valve, as for testing, or draining the lines

        when run as a module, valveControl assumes GPIO is setup as defined in cageSet and offers to open/close water
        delivery solenoid. ValveControl takes an instance of AHF_CageSet as a paramater and assumes
        that the GPIO pin connected to the water delivery solenoid us as defined in the cageSet, and
        that GPIO is already setup.
        param:cageSet: an instance of AHF_CageSet describing which pin is used for water reward solenoid
        returns:nothing
        """
        runLoop(cageSet)

def runLoop(cageSet):
    """
    main loop asks user to open or close solenoid; Opens on 1, closes on 0, quits on q

    param:cageSet: an instance of AHF_CageSet describing which pin is used for water reward solenoid
    returns:nothing
    """
    try:
        while (True):
            s = input("1 to open, 0 to close, q to quit: ")
            if s == '1':
                print ("valve is open")
                GPIO.output(cageSet.rewardPin, 1)
            elif s == '0':
                 print ("valve is closed")
                 GPIO.output(cageSet.rewardPin, 0)
            elif s == 'q':
                print ("AHF_ValveControl quitting")
                break
            else:
                print ("I understand 1 for open, 0 for close, q for quit.")
    except KeyboardInterrupt:
        print ("i also quit")
        return
    finally:
        if __name__ == '__main__':
            GPIO.cleanup() # this ensures a clean exit
            print ('cleanup')


if __name__ == '__main__':
    valveControl ()
