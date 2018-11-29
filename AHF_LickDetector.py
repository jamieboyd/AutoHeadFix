#! /usr/bin/python
#-*-coding: utf-8 -*-

from time import time, sleep
from datetime import datetime
import RPi.GPIO as GPIO
import Adafruit_MPR121.MPR121 as MPR121

"""
Adafruit_MPR121 requires the Adafuit MPR121 library which, in turn,
requires the Adafuit GPIO library
git clone https://github.com/adafruit/Adafruit_Python_MPR121
git clone https://github.com/adafruit/Adafruit_Python_GPIO

imports Adafruit_GPIO for the i2c library. The file
/Adafruit_Python_GPIO/Adafruit_GPIO/Adafruit_GPIO/I2C.py contains a function,
require_repeated_start, that fails with newer OS verions. It tries to edit
a file, '/sys/module/i2c_bcm2708/parameters/combined', that may no longer exist.
Replace the file name with '/sys/module/i2c_bcm2835/parameters/debug' reinstall,
and try again.

        subprocess.check_call('chmod 666 /sys/module/i2c_bcm2835/parameters/debug', shell=True)
        subprocess.check_call('echo -n 1 > /sys/module/i2c_bcm2835/parameters/debug', shell=True)
"""

class LickDetector (object):
    """
    Lick detector can do two things - 1) continuously log lick times, and 2) wait for a lick. Or both at the same time with waitForLick_Soft
    """
    def __init__(self):
        # initialize capacitive sensor gobal object and start it up
        self.mpr121 = MPR121.MPR121()
        self.mpr121.begin()
        self.mpr121.set_thresholds (8,4) # as per dirkjan
        self.hasCallBack = False

    def getTouches ():
        return self.mpr121.touched ()


    def waitForLick_Hard (self, timeOut_secs, startFromZero=True):
        """
        Waits for a lick on any channel
        Do not call this function if the callback is installed
        """
        if self.hasCallBack:
            return None
        touched = self.mpr121.touched ()
        if touched > 0:
            if not startFromZero:
                return touched
            else:
                endTime = time() + timeOut_secs
                while time () < endTime and touched > 0:
                    event = GPIO.wait_for_edge (self.IRQ_PIN, GPIO.FALLING, timeout = 50)
                    if event is not None:
                        touched = self.mpr121.touched ()
                # 0 touches, guaranteed, wait for next touch
        event = GPIO.wait_for_edge (self.IRQ_PIN, GPIO.FALLING, timeout = 1000 * timeOut_secs)
        return self.mpr121.touched ()


    def installCallback (self, IRQ_PIN, data_logger)

        self.IRQ_PIN = IRQ_PIN
        # set up IRQ interrupt function. GPIO.setmode should alreay have been called
        GPIO.setup(self.IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.isLogging =False
        if data_logger is None:
            self.data_logger = Simple_Logger (None)
        else:
            self.data_logger= data_logger
        global globalDetector
        globalDetector = self
        GPIO.setmode (GPIO.BCM)
        GPIO.setup (IRQ_PIN, GPIO.IN)
        GPIO.add_event_detect (IRQ_PIN,  GPIO.FALLING)
        GPIO.add_event_callback (IRQ_PIN, AHF_LickDetectorCallback)        
        self.hasCallBack = True
        # state of touches from one invocation to next
        self.prevTouches = self.mpr121.touched()
        # global variable to start counting licks
        global g_licks_soft_start

    def removeCallback (self):
        GPIO.remove_event_detect (self.IRQ_PIN)
        
        """
        global gLickTouches
        gLickTouches = 0
        
        global g_licks_detected []
        g_licks_detected =0
        global g_lick_last_data
        g_lick_last_data =0
        global g_lick_channels
        g_lick_channels = channel_numbers
        global g_licks_logger
        g_licks_logger = data_logger # data logger is AHF_Datalogger object, or eqivalent
        """





"""
    Global variables for callback function that does the checking of the lick detector
    
"""
gLickDetector = None        # will be initialized with MPR121 capacitive sensor object
g_lickTouches = 0           # raw state of touch sensor
g_hotLicks = 0              # channels with licks freshly reporting, will be reset at next invocation of lick detector call back


g_licks_detected = 0        # constantly updated with latest lick detection from callback 
g_lick_channels = ()        # tuple of channels reporting licks
g_lick_last_data = 0        # results from last run of callback. Used to compare to result from this callback, only report lick on, not off
g_licks_logger = None       # AHF_Datalogger object, or eqivalent, to do whatever logging you want to do
g_licks_soft_start =0       # set to 1 when waiting for a lick, or 0 when done waiting
g_licks_soft_num =0


def AHF_LickDetectorCallback (channel):
    global globalDetector
    global g_hotLicks
    
    global g_lick_channels
    global g_lick_last_data
    global g_licks_detected
    global g_licks_soft_start
    global g_licks_soft_num

    nowTouches = gLickDetector.getTouches ()
    g_hotLicks = 0

    chanBit = 1
    for channel in range (0,10):
        if not (gLickDetector.prevTouches & chanBit) and (nowTouches & chanBit):
            g_hotLicks += chanBit
        chanBit << 1
    self.prevTouches = nowTouches


            
    g_lick_last_data = touched
    if g_licks_detected > 0:
        if g_licks_soft_start == 1:
            g_licks_soft_num += g_licks_detected
        if g_licks_logger is not None:
            g_licks_logger.writeToLogFile('lick:' + str (g_licks_detected))
    

    
        chanBits = 2**channel



    def set_mouse (self, mouse):
        global g_mouse
        g_mouse = mouse
    
    def start_logging (self):
        if self.isLogging == False:
            GPIO.add_event_detect(self.IRQ_PIN, GPIO.FALLING)
            GPIO.add_event_callback (self.IRQ_PIN, AHF_LickDetectorCallback)        
            self.isLogging = True

    def stop_logging (self):
        if self.isLogging == True:
            GPIO.remove_event_detect (self.IRQ_PIN)
            self.isLogging = False  

    def waitForLick_Soft (self, timeOut_secs, startFromZero=False):
        global g_licks_soft_start
        global g_licks_soft_num
        g_licks_soft_num =0
        g_licks_soft_start =1
        endTime = time() + timeOut_secs
        while time () < endTime and g_licks_soft_num == 0:
            sleep (0.01)
        returnVal = g_licks_soft_num
        g_licks_soft_start = 0
        return returnVal

    def countLicks_Soft (self, time_secs):
        global g_licks_soft_start
        global g_licks_soft_num
        g_licks_soft_num =0
        g_licks_soft_start = 1
        sleep (time_secs)
        returnVal =g_licks_soft_num
        return returnVal 

 
    def test (self, cageSet):
        self.start_logging ()
        print ('\nLick detetctor waiting 10 seconds for a touch....')
        lick = self.waitForLick_Soft (10, True)
        if lick == 0:
            inputStr= input('No licks detected. Do you want to change IRQ pin, currently ' + str (cageSet.lickIRQ) + ":")
            if inputStr[0] == 'y' or inputStr[0] == "Y":
                GPIO.remove_event_detect (self.IRQ_PIN)
                cageSet.lickIRQ = int (input('Enter New Lick Detector IRQ pin:'))
                self.IRQ_PIN = cageSet.lickIRQ
                GPIO.setup(self.IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        sleep (0.2)
        self.stop_logging ()

        
class Simple_Logger (object):
    def __init__(self, logFP):
        self.logFP = logFP

    
    def writeToLogFile(self, event):
        outPutStr = '{:013}'.format(0)
        
        logOutPutStr = outPutStr + '\t' + '{:.2f}'.format (time ())  + '\t' + event +  '\t' + datetime.fromtimestamp (int (time())).isoformat (' ')
        printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
        print (printOutPutStr)
        if self.logFP is not None:
            self.logFP.write(logOutPutStr + '\n')
            self.logFP.flush()

if __name__ == '__main__':
    import RPi.GPIO as GPIO
    from AHF_LickDetector import AHF_LickDetector
    from RFIDTagReader import TagReader
    from AHF_DataLogger import AHF_DataLogger
    # constants for hardware
    serialPort = '/dev/ttyUSB0'
    tag_in_range_pin=17
    lick_IRQ_pin = 26
    try:
        GPIO.setmode(GPIO.BCM)
        # a minimal dict for data logger
        task={'cageID':'c17', 'dataPath':'/home/pi/Documents/'}
        logger = AHF_DataLogger (task)
        logger.newDay (None)
        ld = AHF_LickDetector ((0,1),lick_IRQ_pin,logger)
        tagReader = TagReader(serialPort, True, timeOutSecs = 0.05, kind='ID')
        tagReader.installCallBack (tag_in_range_pin)

    
        ld.start_logging ()
        print ('Licks in 30 seconds...')
        print ('=', ld.countLicks_Soft (30))
        """
        for i in range (0, 5):
            print ('soft wait no-zero #' +  str (i) + ' : ' + str(ld.waitForLick_Soft (5, False)))
        for i in range (0, 5):
            print ('soft wait zero #' +  str (i) + ' : ' + str(ld.waitForLick_Soft (5, True)))
        ld.stop_logging ()
        for i in range (0, 5):
            print ('hard  wait zeroed #' +  str (i) + ' : '  + str(ld.waitForLick_Hard (5, True)))
        for i in range (0, 5):
            print ('hard  wait not zeroed #' +  str (i) + ' : '  + str(ld.waitForLick_Hard (5, False)))
            sleep (0.1)
        """
        GPIO.remove_event_detect(tag_in_range_pin)
        GPIO.cleanup()
    except Exception as e:
        GPIO.remove_event_detect(tag_in_range_pin)
        GPIO.cleanup()
