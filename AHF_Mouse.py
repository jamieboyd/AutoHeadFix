#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Task import Task
import AHF_ClassAndDictUtils as CAD
from AHF_TagReader import AHF_TagReader


class Mice:
    """
    The Mice class contains an array of Mouse objects, plus a reference to the Task object
    """
    def __init__(self, task):
        """
        Initializes the array of mice, from a config file path, with an empty array, and keeps a reference to the task object
        """
        if task.mouseConfigPath
        self.mouseArray=[]
        self.task = task
    
    
    def
    
    
    def userConfigure (self):
        """
            Allows user to add mice to file, maybe use TagReader, give initial values to paramaters
            """
        while True:
            inputStr = '\n************** Mouse Configuration ********************\nEnter:\n'
            inputStr += 'R to read a tag from the Tag Reader and add that mouse\n'
            
            inputStr += 'P to print current stats for all mice\n'
            event = input (inputStr)
                if event == 'r' or event == 'R':
                    tag = self.task.TagReader.readTag()


class Mouse:
    """
    Class to hold information about each mouse, each mouse gets its own object. mouse data
    is updated and stored, as in a JSON config file, for each mouse, updated after each entry
    so it can be reloaded if program needs to be stopped
    """
    def __init__(self, tag, entries, entranceRewards, headFixes, headFixRewards):
        """
        Makes a new mouse object, initializing with RFID tag and entrance and reward info

        entrance and reward info can be loaded from quickStats file if program is restarted, else each
        mouse will probably be initialized with 1 entry, all reward 0 first time mouse enters chamber
        :param tag: RFID tag of this mouse
        :param entries: number of entries mouse has made
        :param entranceRewards: number of entrance rewards mouse has been given
        :param headFixes: number of head fixes for this mouse
        :param headFixRewards: number of head fix rewards mouse has earned

        """
        self.tag = tag
        self.entries = entries
        self.tot_entries = entries
        self.entranceRewards = entranceRewards
        self.headFixes = headFixes
        self.headFixRewards = headFixRewards
        self.stimResultsDict = {}

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



    




    def addMouse (self, aMouse, statsfp):
        """
        Appends a mouse object to the array and updates quickstats file with new mouse
        :param aMouse: the mouse object to append
        :param statsfp: file pointer to the quickstats file so it can be updated
        """
        for mouse in self.mouseArray:
            if mouse.tag == aMouse.tag:
                print ('Mouse with tag ' + str (aMouse.tag) + ' has already been added')
                return -1
        self.mouseArray.append(aMouse)
        # add a blank line to the quik stats file
        if statsfp is not None:
            statsfp.seek (39 + 38 * len (self.mouseArray))
            outPutStr = '{:013}'.format(int (aMouse.tag)) + "\t" +  '{:05}'.format(0) + "\t" +  '{:05}'.format(0) + "\t"
            outPutStr += '{:05}'.format(0) + "\t" + '{:05}'.format(0) + "\n"
            statsfp.write (outPutStr)
            statsfp.flush()
        aMouse.arrayPos = len (self.mouseArray)-1


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
        for mouse in self.mouseArray:
            if mouse.tag == tag:
                self.mouseArray.remove (mouse)
                return len (self.mouseArray)
        #print ('Mouse with tag ' + str (aMouse.tag) + ' was not found.')
        return -1


    def show (self):
        """
        Prints the info for each mouse in the array by calling mouse.show
        """
        print ('nMice = ' + str (len(self.mouseArray)))
        for mouse in self.mouseArray:
            mouse.show()

    def clear (self):
        """
        Clears the info for each mouse in the array by calling mouse.clear
        """
        for mouse in self.mouseArray:
            mouse.clear()
 

    def getMouseFromTag (self, tag):
        """
        Finds the mouse with the given tag number from the array of mice
        
        :param tag: the tag ID of the  mouse to find
        :returns: the mouse object with the given tag
        """
        for mouse in self.mouseArray:
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
        for mouse in self.mouseArray:
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
        return len (self.mouseArray)

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
