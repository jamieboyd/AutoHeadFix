#! /usr/bin/python
#-*-coding: utf-8 -*-
"""
AHF_CageSet defines functions for copying settings between the AHFconfig.jsn text file and the task object
Cage Settings are settings specific to a particular setup, hardware pinouts, file paths for saving/loading data, and cage ID

"""

import json
import os
import pwd
import grp
from AHF_HeadFixer import AHF_HeadFixer

def load (task):
     try:
          with open ('AHFconfig.jsn', 'r') as fp:
               data = fp.read()
               data=data.replace('\n', ',')
               configDict = json.loads(data);print (configDict)
               fp.close()
               setattr (task, 'cageID', configDict.get('Cage ID'))
               setattr (task, 'headFixer', configDict.get('Head Fixer'))
               AHF_HeadFixer.get_class (task.headFixer).configDict_read (task, configDict)
               setattr (task, 'rewardPin', configDict.get('Reward Pin'))
               setattr (task, 'tirPin', configDict.get('Tag In Range Pin'))
               setattr (task, 'contactPin', configDict.get('Contact Pin'))
               setattr (task, 'contactPolarity', configDict.get('Contact Polarity')) # RISING or FALLING, GPIO.RISING = 31, GPIO.FALLING = 32
               setattr (task, 'contactPUD', configDict.get('Contact Pull Up Down')) # OFF, DOWN, or UP, GPIO.PUD_OFF=20, GPIO.PUD_DOWN =21, GPIO.PUD_UP=22
               setattr (task, 'ledPin', configDict.get('LED Pin')) # OFF, DOWN, or UP, GPIO.PUD_OFF=20, GPIO.PUD_DOWN =21, GPIO.PUD_UP=22
               setattr (task, 'contactPin', configDict.get('Contact Pin'))
               setattr (task, 'serialPort', configDict.get('Serial Port'))
               setattr (task, 'lickIRQ', configDict.get('lick IRQ Pin'))   # or -1 if we dont have a lick sensor
               setattr (task, 'dataPath', configDict.get('Path to Save Data'))
               setattr (task, 'mouseConfigPath', configDict.get('Path to Mouse Config Data'))
               setattr (task, 'entryBBpin', configDict.get('Entry Beam Break Pin'))
     except (TypeError, IOError) as e: #we will make a file if we didn't find it, or if it was incomplete
          print ('Unable to open base configuration file, AHFconfig.jsn, let\'s make new settings.\n')
          setattr (task, 'cageID', input('Enter the cage ID:'))
          setattr (task, 'headFixer', AHF_HeadFixer.get_HeadFixer_from_user())
          AHF_HeadFixer.get_class (task.headFixer).config_user_get (task)
          setattr (task, 'rewardPin', int (input ('Enter the GPIO pin connected to the water delivery solenoid:')))
          setattr (task, 'contactPin', int (input ('Enter the GPIO pin connected to the headbar contacts or IR beam-breaker:')))
          contactInt = int (input ('Enter the contact polarity, 0=FALLING for IR beam-breaker or falling polarity electrical contacts, 1=RISING for rising polarity elctrical contacts:'))
          if contactInt == 0:
               setattr (task, 'contactPolarity', 'FALLING')
          else:
               setattr (task, 'contactPolarity', 'RISING')
          contactInt = int (input('Enter desired resistor on contact pin, 0=OFF if external resistor present, else 1=DOWN if rising polarity electrical contact or 2 = UP if IR beam-breaker or falling polarity electrical contacts:'))
          if contactInt ==0:
               setattr (task, 'contactPUD', 'OFF')
          elif contactInt == 1:
               setattr (task, 'contactPUD', 'DOWN')
          else:
               setattr (task, 'contactPUD', 'UP')
          setattr (task, 'ledPin', int (input ('Enter the GPIO pin connected to the blue LED for camera illumination:')))
          setattr (task, 'serialPort' , input ('Enter serial port for tag reader(likely either /dev/Serial0 or /dev/ttyUSB0):'))
          setattr (task, 'tirPin', int (input ('Enter the GPIO pin connected to the Tag-in-Range pin on the Tag reader:')))
          setattr (task, 'dataPath', input ('Enter the path to the directory where the data will be saved:'))
          hasEntryBB = input('Does the experimental tube have a beam break at the entry, (yes or no):')
          if hasEntryBB [0] == 'Y' or hasEntryBB [0] == 'y':
               setattr (task, 'entryBBpin', int (input ('Enter the GPIO pin connected to the beam break at the tube entrance:')))
          else:
               delattr (task, entryBBpin)
          AHF_CageSet.show(task)
          doSave = input ('Enter \'e\' to re-edit the new Cage settings, or any other character to save the new settings to a file.')
          if doSave == 'e' or doSave == 'E':
           self.edit()
          else:
           self.save()
          return

def save(task):
   """
   Saves current configuration stored in the task object into the file ./AHFconfig.jsn

   Call this function after modifying the contents of the task to save your changes

      :param: none
      :returns: nothing
   """
   jsonDict={'Cage ID':task.cageID,'Head Fixer':task.headFixer}
   AHF_HeadFixer.get_class (task.headFixer).configDict_set (task, jsonDict)
   jsonDict.update ({'Reward Pin':task.rewardPin, 'Tag In Range Pin':task.tirPin, 'Contact Pin':task.contactPin})
   jsonDict.update ({'Contact Polarity':task.contactPolarity, 'Contact Pull Up Down':task.contactPUD})
   jsonDict.update ({'LED Pin' : task.ledPin, 'Serial Port' : task.serialPort, 'Path to Save Data':task.dataPath, 'Mouse Config Path':task.mouseConfigPath})
   jsonDict.update ({'Has Entry Beam Break':task.hasEntryBB})
   if hasattr(task, 'entryBBpin'):
       jsonDict.update ({'Entry Beam Break Pin':task.entryBBpin})
   with open ('AHFconfig.jsn', 'w') as fp:
       fp.write (json.dumps (jsonDict))
       fp.close ()
       uid = pwd.getpwnam ('pi').pw_uid
       gid = grp.getgrnam ('pi').gr_gid
       os.chown ('AHFconfig.jsn', uid, gid) # we may run as root for pi PWM, so we need to expicitly set ownership

def show (task):
   """
   Prints the current configuration stored in this AHF_CageSet to the console, nicely formatted

      :param: none
      :returns: nothing
   """
   print ('****************Current Auto-Head-Fix Cage Settings********************************')
   print ('1:Cage ID=' + str (task.cageID))
   print ('2:Head Fix method=' + task.headFixer)
   print ('3:' + AHF_HeadFixer.get_class (task.headFixer).config_show(self))
   print ('4:Reward Solenoid Pin=' + str (task.rewardPin))
   print ('5:Tag-In-Range Pin=' + str (task.tirPin))
   print ('6:Contact Pin=' + str(task.contactPin))
   print ('7:Contact Polarity =' + str(task.contactPolarity) + ' and contact Pull Up Down = ' + str(self.contactPUD))
   print ('8:Brain LED Illumination Pin=' + str(task.ledPin))
   print ('9:Tag Reader serialPort=' + task.serialPort)
   print ('10:dataPath=' + task.dataPath)
   print ('11:Has Entry Beam Break=' + str (task.hasEntryBB))
   if hasattr(task, 'entryBBpin'):
       print ('12:Entry Beam Break Pin=' + str (task.entryBBpin))
   print ('**************************************************************************************')


def edit (task):
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
       elif editNum == 11:
           self.hasEntryBB = bool (input('The experimental tube has a beam break at the entry, True or False:'))
       elif editNum ==12:
           self.entryBBpin = int (input ('Enter the GPIO pin connected to the beam break at the tube entrance:'))
       else:
           print ('I don\'t recognize that number ' + str (editNum))
   self.show()
   self.save()
   return


## for testing purposes
if __name__ == '__main__':
     import AHF_CageSet
     task = None
     AHF_CageSet.load (task)
     print ('Cage ID:', task.cageID,'\tContact Pin:', task.contactPin, '\tContact PUD:', task.contactPUD, '\n')
     AHF_CageSet.edit(task)
     AHF_CageSet.save(task)
