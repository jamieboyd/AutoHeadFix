#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Task import Task
import AHF_ClassAndDictUtils as CAD
from AHF_Reader import AHF_Reader
from AHF_Base import AHF_Base

class Mice (object):
    """
    The Mice class contains a dictionary of Mouse configuration dictionaries, plus a reference to the Task object
    Mouse configuration dictionaries may have appended dictionaries as follows:
    Dictionaries from Stimulator, 1 for results, stimResults, and 1 for parameters, stimParams
    Dictionary from HeadFixer, either headFix% or headFix type (loose, strong, a scale from 1 -8)
    Dictionary from Rewarder, task and entry reward size, max entry rewards, daily reward totals
    """

    def __init__(self, task):
        """
        Initializes the list of mice with an empty list, or from configuration from DataLogger, and keeps a reference to the task object
        """
        self.task = task # reference to the task where all objects are referenced
        self.currentMouse = None # reference to current mouse in the array, thae one that is in the experimental tube
        if hasattr (self.task, 'DataLogger'): # try to load mice configuration from dataLogger
            self.mouseList=self.task.DataLoger.loadAllMiceData ()
        else:
            self.mouseList=[]





    def userConfigure (self):
        """
        Allows user to add mice to file, maybe use TagReader, give initial values to paramaters
        """
        while True:
            inputStr = '\n************** Mouse Configuration ********************\nEnter:\n'
            inputStr += 'A to add a mouse, by its RFID Tag\n'
            inputStr += 'T to read a tag from the Tag Reader and add that mouse\n'
            inputStr += 'P to print current daily stats for all mice\n'
            inputStr += 'R to remove a mouse from the list, by RFID Tag\n: '
            event = input (inputStr)
            tag = 0
            if event == 'p' or event == 'P': # print mice stats
                self.showMice ()
            elif event == 'r' or event == 'R': # remove a mouse
                tag = input ('Enter the RFID tag of the mouse to be removed: ')
                wasFound = False
                for mouse in self.mouseList:
                    if mouse.tag == tag:
                        self.mouseList.remove (mouse)
                        wasFound = True
                        break
                if not wasFound:
                    print ('Mouse with tag ' + str (tag) + ' was not found.')
            else: # other two choices are for adding a mouse by RFID Tag, either reading from Tag Reader, or typing it
                if event == 't' or event == 'T':
                    tag = self.task.TagReader.readTag()
                elif event == 'a' or event == 'A':
                    tag = int(input ('Enter the RFID tag for new mouse: '))





    def tagExists (self, RFIDTag):
        """
        Returns True if a mouse with the same RFID Tag isd already in the mice list
        """
        for mouse in self.mouseList:
            if mouse.tag == RFIDTag:
                print ('A mouse with tag ' + str (mouse.tag) + ' has already been added.')
                return True
        return False


    def showMice (self):
        stimDictKeys = self.mouseList [0].stimResultsDict.keys()
        print ('Mouse\tEntries\tEntry Rewards\tHeadFixes\tHeadFix Rewards'.join('\t' + key for key in stimDictKeys))
        for mouse in self.mouseList:
            printStr = '{:013}\t{:d}\t{:d}\t{:d}\t{:d}'.format(self.tag, self.entries, self.headFixes, self.entranceRewards, self.headFixRewards)
            printStr.join ('\t' + str(self.mouseList [0].stimDict.get(key)) for key in stimDictKeys)
            print (printStr)


    def userAddMouse (self, tag):
        """
        Appends a mouse object to the array and updates quickstats file with new mouse
        :param tag: the mouse's RFID tag, must be unique
        """

        aMouse = Mouse (tag, stimResultsDict = {})
        self.mouseList.append(aMouse)
        # add a blank line to the quik stats file
        if statsfp is not None:
            statsfp.seek (39 + 38 * len (self.mouseList))
            outPutStr = '{:013}'.format(int (aMouse.tag)) + "\t" +  '{:05}'.format(0) + "\t" +  '{:05}'.format(0) + "\t"
            outPutStr += '{:05}'.format(0) + "\t" + '{:05}'.format(0) + "\n"
            statsfp.write (outPutStr)
            statsfp.flush()
        aMouse.arrayPos = len (self.mouseList)-1


class Mouse:
    """
    Class to hold information about each mouse, each mouse gets its own object. mouse data
    is updated and stored, as in a JSON config file, for each mouse, updated after each entry
    so it can be reloaded if program needs to be stopped
    """
    def __init__(self, tag, StimulatorResultsDict, RewarderResultsDict, headFixerResultsDict, StimulatorDict = None, RewarderDict = None, headFixerDict = None):
        """
        Makes a new mouse object, initializing with RFID tag and entrance and reward info

        entrance and reward info can be loaded from quickStats file if program is restarted, else each
        mouse will probably be initialized with 1 entry, all reward 0 first time mouse enters chamber
        :param tag: RFID tag of this mouse
        """
        self.tag = tag
        self.entries = 0 # no object that tracks entries, so we track them separately
        self.StimulatorDict = StimulatorDict #
        self.StimulatorResultsDict = StimulatorResultsDict
        self.RewarderDict = RewarderDict # params for rewarder, specialized for this mouse, e.g., reward sizes, reward limits
        self.RewarderResultsDict = RewarderResultsDict # rewarder results, e.g. number of rewrads of different types given to this mouse
        self.headFixerDict =headFixerDict
        self.headFixerResultsDict =headFixerResultsDict




    def clear (self):
        """
        Clears the stats for entries and rewards for this mouse, done at the start of every day
        Also clears any StimResults dict entries that the stimulator has made
        """
        self.entries = 0
        self.headFixes = 0
        self.entranceRewards = 0
        self.headFixRewards = 0
        if self.stimResultsDict is not None:
            for key in self.stimResultsDict:
                self.stimResultsDict [key] = 0

    def reward (self, rewarder, rewardName):
        """
        Gives a reward to the mouse and increments the reward count for task or entries
        :param:rewarder: Rewarder object used to ive rewards for all the mice
        :param rewardName: either entrance or task for the two types of rewards logged
        """
        rewarder.giveReward (rewardName)
        if rewardName == 'entrance':
            self.entranceRewards +=1
        elif rewardName == 'task':
            self.headFixRewards += 1


    def show (self):
        """
        Prints all the data for this mouse, including any stimResults info
        """
        print ('MouseID:', '{:013}'.format(self.tag), '\tEntries:', self.entries, '\tHeadFixes:', self.headFixes, '\tEntRewards:', self.entranceRewards, '\tHFRewards:',self.headFixRewards)
        if self.stimResultsDict is not None:
            stimResults = 'Stim Results:'
            for key in self.stimResultsDict:
                stimResults += '\t' + key + ":" + str (self.stimResultsDict.get (key))
            print (stimResults)











    def addMiceFromFile(self):
        """
        Adds mouse objects to the mice array, initialzing tagID and initial values for rewards from quickstats file

        If there is a problem with the quickstats file structure, the file is scrubbed and started over with 0 mice
        :param statsfp: file pointer to the quickstats file
        returns:nothing
        """



    def removeMouseByTag (self, tag):
        """
        Removes the mouse with the given tag number from the array of mice
        :param tag: the tag ID of the  mouse to remove
        """
        for mouse in self.mouseList:
            if mouse.tag == tag:
                self.mouseList.remove (mouse)
                return len (self.mouseList)
        #print ('Mouse with tag ' + str (aMouse.tag) + ' was not found.')
        return -1


    def show (self):
        """
        Prints the info for each mouse in the array by calling mouse.show
        """
        print ('nMice = ' + str (len(self.mouseList)))
        for mouse in self.mouseList:
            mouse.show()

    def clear (self):
        """
        Clears the info for each mouse in the array by calling mouse.clear
        """
        for mouse in self.mouseList:
            mouse.clear()


    def getMouseFromTag (self, tag):
        """
        Finds the mouse with the given tag number from the array of mice

        :param tag: the tag ID of the  mouse to find
        :returns: the mouse object with the given tag
        """
        for mouse in self.mouseList:
            if mouse.tag == tag:
               return mouse
        #print ('No mouse with tag ' + str (tag) + ' is in the array')
        return None


    def getMousePos (self, tag):
        """
        Finds the positon in the array of the mouse with the given tag number
        :param tag: the tag ID of the  mouse to remove
        :returns: the position with the array
        """
        iPos =0
        for mouse in self.mouseList:
            if mouse.tag == tag:
               return ipos
            iPos +=1
        #print ('No mouse with tag ' + str (tag) + ' is in the array')
        return -1

    def nMice(self):
        """
        gets the number of mice in the mouse array
        :returns: the number of mice in the array
        """
        return len (self.mouseList)

#for testing
if __name__ == '__main__':
    m1= Mouse (16, 0,0,0,0, None)
    m2 = Mouse (17, 0,0,0,0, None)
    m1.show()
    m2.show()
    mArray = Mice()
    mArray.addMouse (m1, None)
    mArray.addMouse (m2, None)
    mArray.addMouse (m1, None)
    mArray.show()
    mTemp = mArray.getMouseFromTag (17)
    mTemp.show()
    rewardPin= 18
    GPIO.setwarnings(False)
    GPIO.setmode (GPIO.BCM)
    rewarder = AHF_Rewarder (30e-03, rewardPin)
    rewarder.addToDict('entrance', 20e-03)
    rewarder.addToDict('task', 60e-03)
    rewarder.addToDict('entrance', 20e-03)
    mTemp.reward (rewarder, 'task')
    mTemp = mArray.getMouseFromTag (16)
    mTemp.entries +=1
    mTemp.headFixes +=1
    if mTemp is not None:
        mTemp.reward (rewarder, 'entrance')
    mTemp = mArray.getMouseFromTag (27)
    if mTemp is not None:
        mTemp.show()
    mArray.show()
    mArray.removeMouseByTag (17)
    mArray.show()
    GPIO.cleanup()
