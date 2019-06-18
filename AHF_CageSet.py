#! /usr/bin/python
#-*-coding: utf-8 -*-

import json
import os
import pwd
import grp
from AHF_HeadFixer import AHF_HeadFixer


class AHF_CageSet (object):

    """
    Manages settings for hardware GPIO pin-outs and some other cage-specific settings for the raspberry Pi used for Auto Head Fix

    The class AHF_CageSet defines the following settings:
       :cage ID: str - whatver name you have for this cage
       :headFixer: str - name of class used for HeadFixing, can be pistons, or servo-motor with pi PWM or AdaFruit I2C PWM driver
       :pistons Pin: int - connected to solenoids that drive pistons for head fixing, (only if using pistons)
       :Servo Address: int- servo address of AdaFruit I2C PWM driver (only if using adafruit servo)
       :PWM CHannel: int- PWM channel (0 or 1) if using pi PWM 
       :servoReleased: int - position of server to release mouse, (only if using adafruit servo)
       :servoFixed: int - position of servo to fix mouse (only if using servo)
       :rewardPin: int - connected to solenoid for delivering water reward
       :tirPin: int - tag in-range pin for the ID tag reader
       :contactMode: str - BeamBreak, or ContactCheck
       :contactPin: int - GPIO connected to the head contacts, or IR beam-breaker
       :ledPin: int - output pin for the Blue LED that illuminates the brain
       :serialPort: str - "/dev/ttyUSB0" for USB with sparkFun breakout or "/dev/ttyAMA0" for built-in
       :dataPath: str - path to base folder, possibly on removable media, where data will be saved in created subfolders
    The settings are saved between program runs in a json-styled text config file, AHFconfig.jsn, in a human readable and editable key=value form.
"""

    def __init__(self):
        """
        Makes a new AHF_CageSet object by loading from AHFconfig.jsn or by querying the user

        Either reads a dictionary from a config file, AHFconfig.jsn, in the same directory in which the program is run,
        or if the file is not found, it querries the user for settings and then writes a new file.

        """
        try:
            with open ('AHFconfig.jsn', 'r') as fp:
                data = fp.read()
                data= data.replace('\n', ",")
                print (data)
                configDict = json.loads(data)
                fp.close()
                self.cageID = configDict.get('Cage ID')
                self.headFixer = configDict.get('Head Fixer')
                headFixerClass = AHF_HeadFixer.get_class (self.headFixer)
                headFixerClass.configDict_read (self, configDict)
                self.rewardPin = int(configDict.get('Reward Pin'))
                self.tirPin = int(configDict.get('Tag In Range Pin'))
                self.contactPin = int (configDict.get ('Contact Pin'))
                self.contactPolarity = configDict.get ('Contact Polarity') # RISING or FALLING, GPIO.RISING = 31, GPIO.FALLING = 32
                self.contactPUD = configDict.get ('Contact Pull Up Down') # OFF, DOWN, or UP, GPIO.PUD_OFF=20, GPIO.PUD_DOWN =21, GPIO.PUD_UP=22
                self.ledPin =  int (configDict.get ('LED Pin'))
                self.serialPort = configDict.get ('Serial Port')
                self.dataPath =configDict.get ('Path to Save Data')
        except (TypeError, IOError) as e:
            #we will make a file if we didn't find it, or if it was incomplete
            print ('Unable to open base configuration file, AHFconfig.jsn, let\'s make a new one.\n')
            self.cageID = input('Enter the cage ID:')
            self.headFixer = AHF_HeadFixer.get_HeadFixer_from_user()
            AHF_HeadFixer.get_class (self.headFixer).config_user_get (self)
            self.rewardPin = int (input ('Enter the GPIO pin connected to the water delivery solenoid:'))
            self.tirPin = int (input ('Enter the GPIO pin connected to the Tag-in-Range pin on the Tag reader:'))
            self.contactPin = int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:'))
            contactInt = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
            if contactInt == 0:
                self.contactPolarity = 'FALLING'
            else:
                self.contactPolarity = 'RISING'
            contactInt = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
            if contactInt ==0:
                self.contactPUD = 'OFF'
            elif contactInt == 1:
                self.contactPUD = 'DOWN'
            else:
                self.contactPUD='UP'
            self.ledPin = int (input ('Enter the GPIO pin connected to the blue LED for camera illumination:'))
            self.serialPort = input ('Enter serial port for tag reader(likely either /dev/ttyAMA0 or /dev/ttyUSB0):')
            self.dataPath = input ('Enter the path to the directory where the data will be saved:')
            self.show()
            doSave = input ('Enter \'e\' to re-edit the new Cage settings, or any other character to save the new settings to a file.')
            if doSave == 'e' or doSave == 'E':
                self.edit()
            else:
                self.save()
        return


    def save(self):
        """
        Saves current configuration stored in this AHF_CageSet object into the file ./AHFconfig.jsn

        Call this function after modifying the contents of the AHF_CageSet to save your changes

           :param: none
           :returns: nothing
        """
        jsonDict={'Cage ID':self.cageID,'Head Fixer':self.headFixer}
        AHF_HeadFixer.get_class (self.headFixer).configDict_set (self, jsonDict)
        jsonDict.update ({'Reward Pin':self.rewardPin, 'Tag In Range Pin':self.tirPin, 'Contact Pin':self.contactPin})
        jsonDict.update ({'Contact Polarity':self.contactPolarity, 'Contact Pull Up Down':self.contactPUD})
        jsonDict.update ({'LED Pin' : self.ledPin, 'Serial Port' : self.serialPort, 'Path to Save Data':self.dataPath})
        with open ('AHFconfig.jsn', 'w') as fp:
            fp.write (json.dumps (jsonDict, separators = ('\n', ':'), sort_keys = True))
            fp.close ()
            uid = pwd.getpwnam ('pi').pw_uid
            gid = grp.getgrnam ('pi').gr_gid
            os.chown ('AHFconfig.jsn', uid, gid) # we may run as root for pi PWM, so we need to expicitly set ownership

    def show (self):
        """
        Prints the current configuration stored in this AHF_CageSet to the console, nicely formatted

           :param: none
           :returns: nothing
        """
        print ('****************Current Auto-Head-Fix Cage Settings********************************')
        print ('1:Cage ID=' + str (self.cageID))
        print ('2:Head Fix method=' + self.headFixer)
        print ('3:' + AHF_HeadFixer.get_class (self.headFixer).config_show(self))
        print ('4:Reward Solenoid Pin=' + str (self.rewardPin))
        print ('5:Tag-In-Range Pin=' + str (self.tirPin))
        print ('6:Contact Pin=' + str(self.contactPin))
        print ('7:Contact Polarity =' + str(self.contactPolarity) + ' and contact Pull Up Down = ' + str(self.contactPUD))
        print ('8:Brain LED Illumination Pin=' + str(self.ledPin))
        print ('9:Tag Reader serialPort=' + self.serialPort)
        print ('10:dataPath=' + self.dataPath)
        print ('**************************************************************************************')


    def edit (self):
        """
        Allows the user to edit and save the cage settings
        """
        while True:
            self.show()
            editNum = int(input ('Enter number of paramater to Edit, or 0 when done to save file:'))
            if editNum == 0:
                break
            elif editNum == 1:
                self.cageID = input('Enter the cage ID:')
            elif editNum == 2:
                self.headFixer = AHF_HeadFixer.get_HeadFixer_from_user()
                AHF_HeadFixer.get_class (self.headFixer).config_user_get (self)
            elif editNum == 3:
                AHF_HeadFixer.get_class (self.headFixer).config_user_get (self)
            elif editNum == 4:
               self.rewardPin = int (input ('Enter the GPIO pin connected to the water delivery solenoid:'))
            elif editNum == 5:
                self.tirPin= int (input ('Enter the GPIO pin connected to the Tag-in-Range pin on the Tag reader:'))
            elif editNum == 6:
                self.contactPin= int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:'))
            elif editNum == 7:
                contactInt = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
                if contactInt == 0:
                    self.contactPolarity = 'FALLING'
                else:
                    self.contactPolarity = 'RISING'
                contactInt = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
                if contactInt ==0:
                    self.contactPUD = 'OFF'
                elif contactInt == 1:
                    self.contactPUD = 'DOWN'
                else:
                    self.contactPUD='UP'
            elif editNum == 8:
                self.ledPin = int (input ('Enter the GPIO pin connected to the blue LED for camera illumination:'))
            elif editNum == 9:
                self.serialPort = input ('Enter serial port for tag reader(likely either /dev/ttyAMA0 or /dev/ttyUSB0):')
            elif editNum == 10:
                self.dataPath = input ('Enter the path to the directory where the data will be saved:')
            else:
                print ('I don\'t recognize that number ' + str (editNum))
        self.show()
        self.save()
        return



## for testing purposes
if __name__ == '__main__':
    hardWare = AHF_CageSet ()
    print ('Cage ID:', hardWare.cageID,'\tContact Pin:', hardWare.contactPin, '\tContact PUD:', hardWare.contactPUD, '\n')
    hardWare.edit()
    hardWare.save()
