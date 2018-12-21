#! /usr/bin/python
#-*-coding: utf-8 -*-

import ptPWM
from abc import ABCMeta, abstractmethod
from array import array
from math import cos, pi

"""
Class controls a hardware Pulse Width Modulation (PWM) channel on the
pi. There are two of them, channel 0 and channel 1,
"""

class PTPWM (object, metaclass = ABCMeta):
    """
    PTPWM, like PTSimpleGPIO, defines constants for accuracy level for timing:
    ACC_MODE_SLEEPS relies solely on sleeping for timing, which may not be accurate beyond the ms scale
    ACC_MODE_SLEEPS_AND_SPINS sleeps for first part of a time period, but wakes early and spins in a tight loop
    until the the end of the period, checking each time through the loop against calculated end time.
    It is more processor intensive, but much more accurate. How soon before the end of the period the thread
    wakes is set by the constant kSLEEPTURNAROUND in gpioThread.h. You need to re-run setup if it is changed.
    ACC_MODE_SLEEPS_AND_OR_SPINS checks the time before sleeping, so if thread is delayed for some reason, the sleeping is
    countermanded for that time period, and the thread goes straight to spinning, or even skips spinning entirely
    """
    ACC_MODE_SLEEPS = 0
    ACC_MODE_SLEEPS_AND_SPINS =1
    ACC_MODE_SLEEPS_AND_OR_SPINS =2

    """
    PTPWM, like PTSimpleGPIO defines constants for initializing with pulse based (low time, high time, number of pulses) or
    frequency based (frequency, duty cycle, total duration) paramaters. Same information, presented in a different way,
    use what is convenient for your application.
    """
    INIT_PULSES =1
    INIT_FREQ=2

    """
    PTPWM defines constants for two PWM modes, Mark/Space, where each period is divided into a single high portion and a low portion
    set by the output value, and Balanced, where high and low ticks are intermixed throughout the period. Use Mark/Space for
    servo motors and Balnced for driving LEDs or, after low pass filtering, for analog outputs.
    """
    PWM_MARK_SPACE =0
    PWM_BALANCED =1

    
    PWM_CLOCK_FREQ = 0

    """
    Because PTPWM is an abstact base class, we explicitly declare the __init__ method to be abstract
    """
    @abstractmethod
    def __init__():
        pass

    @staticmethod
    def set_clock (PWM_freq, pwm_range):
        ptPWM.setClock (PWM_freq, pwm_range)


class PWM_thread (PTPWM, metaclass = ABCMeta):

    @abstractmethod
    def __init__ (self, pwm_channelP, pwm_modeP, pwm_rangeP, thread_frequencyP, dataArraySize, accuracyP):
         pass

    def enable (self, doEnable, isLocking):
        ptPWM.pwmSetEnable (self.pwm, doEnable, isLocking)

    def set_array_size (self, arraySizeLimit, isLocking):
        if arraySizeLimit < len (self.data_array):
            ptPWM.setArraySize (self.pwm, arraySizeLimit, isLocking)

    def set_array_pos (self, arrayPosition, isLocking):
        ptPWM.setArrayPos (self.pwm, arrayPosition, isLocking)

    def set_new_array (self, newArray, isLocking):
        ptPWM.setNewArray (self.pwm, self.newArray, isLocking)
       
    def sin_array (self, sin_freq, sin_amp, is_centered):
        periodSize= int (round (self.thread_frequency/sin_freq))
        arraySize = int (len (self.data_array)/periodSize) * periodSize
        mult = (self.pwm_range * sin_amp)/2
        if is_centered:
            offset = self.pwm_range - sin_amp*self.pwm_range/2 
            print ('periodSize = ', periodSize, 'arraySize=', arraySize, 'mult=', mult, 'offset=', offset)
            for i in range (0, arraySize):
                self.data_array [i] = int (round(offset - (mult * cos (2 *  pi * (i % periodSize)/periodSize))))
                #print (self.data_array [i])
        else:
            for i in range (0, arraySize):
                self.data_array [i] = int (mult * (1- cos (2 *  pi * (i % periodSize)/periodSize)))
        ptPWM.setNewArray (self.pwm, self.data_array, 0)
        ptPWM.setArraySize (self.pwm, arraySize, 0)
        return arraySize
                

    def wait_on_busy(self, waitSecs):
        return ptPWM.waitOnBusy(self.pwm, waitSecs)


class PWM_thread_rep (PWM_thread):

    def __init__ (self, pwm_channelP, pwm_modeP, pwm_rangeP, thread_frequencyP, dataArraySize, accuracyP):
        self.pwm_channel=pwm_channelP
        self.pwm_mode = pwm_modeP
        self.pwm_range = pwm_rangeP
        self.thread_frequency = thread_frequencyP
        self.data_array = array ('i', (0 for i in range (0, dataArraySize)))
        self.pwm = ptPWM.pwmThread (self.pwm_channel, self.pwm_mode, self.pwm_range, 1, thread_frequencyP, dataArraySize, self.data_array, accuracyP)

    def do_a_rep (self):
        ptPWM.doTask (self.pwm)
    
    def do_reps (self, nReps):
        ptPWM.doTasks (self.pwm, nReps)
        

class PWM_thread_inf (PWM_thread):

    def __init__ (self, pwm_channelP, pwm_modeP, pwm_rangeP, thread_frequencyP, dataArraySize, accuracyP):
        self.pwm_channel=pwm_channelP
        self.pwm_mode = pwm_modeP
        self.pwm_range = pwm_rangeP
        self.thread_frequency = thread_frequencyP
        self.data_array = array ('i', (0 for i in range (0, dataArraySize)))
        self.pwm = ptPWM.pwmThread (self.pwm_channel, self.pwm_mode, self.pwm_range, 1, thread_frequencyP, 0, self.data_array, accuracyP)

    def start (self):
        ptPWM.pwmEnable (self.pwm, 1)
        ptPWM.startTrain (self.pwm)
    
    def stop (self):
        ptPWM.stopTrain (self.pwm)
        ptPWM.pwmEnable (self.pwm, 0)
        

class PWM_simple (PTPWM):
    
    def __init__ (self, pwm_channel, pwm_mode, pwm_range):
        self.pwm = ptPWM.pwmSimp (pwm_channel, pwm_mode, pwm_range)

    def set_PWM (self, pwm_value):
        ptPWM.pwmSet (self.pwm, pwm_value)


    def set_enable (self, enable_value):
        ptPWM.pwmEnable (self.pwm, enable_value)

    def get_PWM (self):
        return ptPWM.pwmGetVal (self.pwm)


if __name__ == '__main__':
    from time import sleep
    from PTPWM import PTPWM, PWM_simple, PWM_thread_rep
    pwm_chan =0
    pwm_mode = PTPWM.PWM_MARK_SPACE
    pwm_frequency = 100
    pwm_range = 4096
    PTPWM.set_clock (pwm_frequency, pwm_range)

    
    dim = int (pwm_range * 0.15)
    bright =int (pwm_range * .99)
    print ('bright = ',bright,' dim = ', dim)

    
    myPWM = PWM_simple (pwm_chan, pwm_mode, pwm_range)
    myPWM.set_PWM (dim)
    myPWM.set_enable (1)
    try:
        while True:
            for i in range (dim, bright, 1):
                myPWM.set_PWM (i)
                sleep (0.001)
            for i in range (bright, dim, -1):
                myPWM.set_PWM (i)
                sleep (0.001)
    except KeyboardInterrupt:

        myPWM.set_enable (0)
        #myPWM=None
    
    #now a thread
    #print ('Now a thread')
    """
    thread_frequency = 1000
    sin_freq = 10
    sin_amp = 0.35
    myPWM = PWM_thread_rep (pwm_chan, pwm_mode, pwm_range, thread_frequency, pwm_range, PTPWM.ACC_MODE_SLEEPS_AND_SPINS)

    newDataArraySize = myPWM.sin_array (sin_freq, sin_amp, 1)

    
    myPWM.enable (1, 0)
    myPWM.do_reps(50)
    print ('Wait on busy returned', myPWM.wait_on_busy (60))
    myPWM.enable (0, 0)
    myPWM= None


    myPWM.sin_array (sin_freq * 5, sin_amp, 1)
    myPWM.do_reps(10)
    print ('Wait on busy returned', myPWM.wait_on_busy (60))
    myPWM.enable (0, 0)
    myPWM= None
    """
        
    
    
    
