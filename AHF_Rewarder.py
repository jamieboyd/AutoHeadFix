#! /usr/bin/python

from time import sleep
from PTSimpleGPIO import CountermandPulse

class AHF_Rewarder:
    """
    A class to use a solenoid to deliver water rewards of various sizes

    A dictionary is used to store different opening durations with user-defined names.
    The Rewarder class is inited with a default duration to be used if
    a non-existent key is later requested, and the pin number of the GPIO pin used to
    control the solenoid. Be sure to run GPIO.setmode (GPIO.BCM) before initing the rewarder
    TODO:1)include a measure of flow rate and record/return values in litres delivered, not
    seconds open. 2) make doReward threaded, so main program does not have to stop for long rewards (done)
    """
     
    def __init__ (self, defaultTimeVal, rewardPin):
        """
        Makes a new Rewarder object with a GPIO pin and default opening time

        :param defaultTimeVal: opening suration to be used if requested reward Type is not in dictionary
        :param rewardPin: GPIO pin number connected to the solenoid
        :return: returns nothing
        """
        self.rewardDict = {'default': defaultTimeVal}
        self.rewardPin = rewardPin
        self.cmPulse = CountermandPulse (self.rewardPin, 0, 0, self.rewardDict.get('default'), 1)


    def addToDict(self, rewardName, rewardSize):
        """
        Adds a new reward type with defined size to the dictionary of reward sizes

        param: rewardName: name of new reward type to add
        param:rewardSize: opening duration of solenoid, in seconds        
        """
        self.rewardDict.update({rewardName : rewardSize})
        

    def giveReward(self, rewardName):
        """
        Gives a reward of the requested type, if the requested reward type is found in the dictionary

        If the requested reward type is not found, the default reward size is used
        param:rewardName: the type of the reward to be given, should already be in dictionary
        """
        self.cmPulse.set_delay(0)
        if rewardName in self.rewardDict:
            sleepTime = self.rewardDict.get(rewardName)
        else:
            sleepTime = self.rewardDict.get('default')
        self.cmPulse.set_duration(sleepTime)
        self.cmPulse.do_pulse()
        
       

    def giveRewardCM(self, rewardName, delayTime):
        """
        Gives a reweard after a delay period, during delay period reward can be countermanded
        
        :param rewardName: the type of the reward to be given, should already be in dictionary
        :param delayTime: delay time during which reward can be countermanded
        """
        if rewardName in self.rewardDict:
            sleepTime = self.rewardDict.get(rewardName)
        else:
            sleepTime = self.rewardDict.get('default')
        self.cmPulse.set_duration(sleepTime)
        self.cmPulse.set_delay (delayTime)
        self.cmPulse.do_pulse_countermandable()
    
    def countermandReward(self):
        """
        countermands reward by setting class variable to 0
        :returns: truth that the reward was countermanded, i.e. False if reward was already given
        """
        return self.cmPulse.countermand_pulse()


    def valveControl (self):
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
                    self.cmPulse.set_level (1, 0)
                elif s == '0':
                     print ("valve is closed")
                     self.cmPulse.set_level (0, 0)
                elif s == 'q':
                    print ("valveControl quitting")
                    break
                else:
                    print ("I understand 1 for open, 0 for close, q for quit.")
        except KeyboardInterrupt:
            print ("ctrl-c also quits")
            return


    def __del__(self):
        del self.cmPulse
        
    
    
#for testing purposes
if __name__ == '__main__':
    rewardPin = 13
    rewarder = AHF_Rewarder (30e-03, rewardPin)
    rewarder.addToDict ("entry", 100e-03)
    rewarder.giveReward ("entry")
    sleep(1)
    rewarder.addToDict ("earned", 150e-03)
    rewarder.giveReward ("earned")
    sleep(1)
    rewarder.giveRewardCM ("entry", 2)
    sleep (0.5)
    print (rewarder.countermandReward ())
    sleep (1)
    del rewarder
