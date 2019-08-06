#! /usr/bin/python
#-*-coding: utf-8 -*-
from AHF_Stimulus import AHF_Stimulus
from PTSimpleGPIO import PTSimpleGPIO, Infinite_train, Train
from time import sleep

class AHF_Stimulus_VibMotor (AHF_Stimulus):
    motorPin_def = 25      # GPIO pin used to drive piezo motor for negative feedback
    motorFreq_def = 300    # frequency to drive the motor
    motorDuty_def = 0.8    # duty cycle to drive motor, unbalanced duty cycle gives nasty harmonics
    pulseTime_def = 0.2
    
    @staticmethod
    def about():
        return "Vibrates a motor"
        
    def hardwareTest(self):
        pass

    def trialPrep (self):
        """
        Prepares stimulus for trial: e.g. aligns laser, preps vib. motor, etc
        """
        return True

    def stimulate (self):
        self.motor.start_train()
        sleep(self.pulseTime)
        self.motor.stop_train()
        pass
    
    @staticmethod
    def config_user_get(starterDict= {}):
        motorPin = starterDict.get ('motorPin', AHF_Stimulus_VibMotor.motorPin_def)
        tempInput = input ('Set motor pin (currently {0}): '.format(motorPin))
        if tempInput != '':
            motorPin = int (tempInput)
        starterDict.update ({'motorPin' : motorPin})
        motorFreq = starterDict.get ('motorFreq', AHF_Stimulus_VibMotor.motorFreq_def)
        tempInput = input ('Set motor frequency (currently {0}): '.format(motorFreq))
        if tempInput != '':
            motorFreq = int (tempInput)
        starterDict.update ({'motorFreq' : motorFreq})
        motorDuty = starterDict.get ('motorDuty', AHF_Stimulus_VibMotor.motorDuty_def)
        tempInput = input ('Set motor duty cycle (currently {0}): '.format(motorDuty))
        if tempInput != '':
            motorDuty = float (tempInput)
        starterDict.update ({'motorDuty' : motorDuty})
        pulseTime = starterDict.get ('pulseTime', AHF_Stimulus_VibMotor.pulseTime_def)
        tempInput = input ('Set pulse length (currently {0}): '.format(pulseTime))
        if tempInput != '':
            pulseTime = float (tempInput)
        starterDict.update ({'pulseTime' : pulseTime})
        return starterDict
    
    def setup(self):
        self.motorPin=int(self.settingsDict.get ('motorPin', self.motorPin_def))
        self.motorFreq=float(self.settingsDict.get ('motorFreq', self.motorFreq_def))
        self.motorDuty = float(self.settingsDict.get ('motorDuty', self.motorDuty_def))
        self.pulseTime = float(self.settingsDict.get ('pulseTime', self.pulseTime_def))
        self.motor=Infinite_train (PTSimpleGPIO.MODE_FREQ, self.motorPin, self.motorFreq, self.motorDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        pass
    
    def setdown(self):
        pass

    def trialEnd (self):
        """
        Code to be run at end of trial. E.g. moving laser to zero position
        """
        pass


