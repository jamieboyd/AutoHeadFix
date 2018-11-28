#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import AHF_Task
from AHF_HeadFixer import AHF_HeadFixer
from time import sleep

class AHF_HeadFixer_PWM (AHF_HeadFixer, metaclass = ABCMeta):
    """
    Abstract class for PWM-based head fixers for servo motors. As long as you map your PWM range onto
    the appropriate pulse width for the servo, you should be good to go.
    """
    hasLevels = True

    ##################################################################################
    #part 1: three main methods of initing, fixing, and releasing, only initing is different for different PWM methods
    @abstractmethod
    def __init__(self, task):
        self.servoReleasedPosition = task.servoReleasedPosition
        self.servoFixedPosition = task.servoFixedPosition
        self.servoIncrement = int ((task.servoReleasedPosition - task.servoFixedPosition)/5)

    # with progressive head fixing. typical servo values 325 =fixed, 540 = released
    # 8 different levels of fixing tightness
    def fixMouse(self, headFixationType = 8):
        # tighter and tighter fixing
        if headFixationType == 0:
            return
        elif headFixationType < 5:
            target = self.servoReleasedPosition -  headFixationType * self.servoIncrement
            start = min (self.servoReleasedPosition, target + (2 * self.servoIncrement))
            print ('start=' + str (start) + ' and target='  + str (target))
            for i in range(start, target, -1):
                self.setPWM (i)
                sleep(0.01)
        elif headFixationType < 8:
        # Get a little closer to the bar and retract
            target = self.servoFixedPosition + int ((7 - headFixationType) * self.servoIncrement/2)
            start = target + self.servoIncrement
            retract = target + int (self.servoIncrement/(headFixationType - 4))
            print ('start=' + str (start) + ', target='  + str (target) + ' and retract = ' + str (retract))
            for i in range(start, target, -1):
                self.setPWM (i)
                sleep(0.01)
            for i in range(target, retract, 1):
                self.setPWM (i)
                sleep(0.01)
        else:
            target =self.servoFixedPosition
            start = target + self.servoIncrement
            for i in range(start, target, -1):
                self.setPWM (i)
                sleep(0.01)
                
            
    def releaseMouse(self):
        self.setPWM (self.servoReleasedPosition)

    # each PWM subclass must implement its own code to set the pulse width
    @abstractmethod
    def setPWM (self, servoPosition):
        pass

  
    ##################################################################################
    #abstact methods each PWM headfixer class must implement
    #part 2: static functions for reading, editing, and saving ConfigDict from/to cageSet
    @staticmethod
    def configDict_read (cageSet,configDict):
        cageSet.servoReleasedPosition = int(configDict.get('Released Servo Position', 815))
        cageSet.servoFixedPosition = int(configDict.get('Fixed Servo Position', 500))

    @staticmethod
    def configDict_set(cageSet,configDict):
        configDict.update ({'Released Servo Position':cageSet.servoReleasedPosition, 'Fixed Servo Position':cageSet.servoFixedPosition}) 
    
    @staticmethod
    def config_user_get (cageSet):
        cageSet.servoReleasedPosition = int(input("Servo Released Position (0-4095): "))
        cageSet.servoFixedPosition = int(input("Servo Fixed Position (0-4095): "))
        
    @staticmethod
    def config_show(cageSet):
        rStr = 'Released Servo Position=' + str(cageSet.servoReleasedPosition)
        rStr += '\n\tFixed Servo Position=' + str(cageSet.servoFixedPosition)
        return rStr
    
    def test (self, cageSet):
        print ('PWM moving to Head-Fixed position for 3 seconds')
        self.fixMouse()
        sleep (3)
        print ('PWM moving to Released position')
        self.releaseMouse()
        inputStr= input('Do you want to change fixed position, currently ' + str (cageSet.servoFixedPosition) + ', or released position, currently ' + str(cageSet.servoReleasedPosition) + ':')
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            cageSet.servoFixedPosition = int (input('Enter New PWM Fixed Position:'))
            cageSet.servoReleasedPosition = int (input('Enter New PWM Released Position:'))
            self.servoReleasedPosition = cageSet.servoReleasedPosition
            self.servoFixedPosition = cageSet.servoFixedPosition
            self.servoIncrement = int ((self.servoReleasedPosition - self.servoFixedPosition)/5)
    

if __name__ == "__main__":
    AHF_HeadFixer.funcForMain()
