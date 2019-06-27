from AHF_Rewarder import AHF_Rewarder
import RPi.GPIO as GPIO
import json
from time import time, localtime
from datetime import datetime,timedelta
import os.path


class Mouse:
    """
    Class to hold information about each mouse, each mouse gets its own object
    """
    def __init__(self, tag, entries, entranceRewards, headFixes, headFixRewards, resultsDict = {}):
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
        self.entranceRewards = entranceRewards
        self.headFixes = headFixes
        self.headFixRewards = headFixRewards
        self.stimResultsDict = resultsDict

    def clear (self):
        """
        Clears the stats for entries and rewards for this mouse, done at the start of every day
        stimulator may clear results at beginning of day as well
        """
        self.entries = 0
        self.headFixes = 0
        self.entranceRewards = 0
        self.headFixRewards = 0
        
    
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
        print ('MouseID:{:013d}\tEntries:{:05d}\tHeadFixes:{:05d}\tHFRewards:{:05d}'.format (self.tag, self.entries, self.headFixes, self.entranceRewards,self.headFixRewards))
        if self.stimResultsDict is not None:
            stimResults = 'Stim Results:\t\t'
            for key in self.stimResultsDict:
                stimResults += '\t' + key + ":" + str (self.stimResultsDict.get (key))
            print (stimResults)



    def updateStats (statsFile):
        """
        Updates the quick stats text file after every exit, mostly for the benefit of folks logged in remotely
        :param statsFile: file pointer to the stats file
        returns:nothing
        """

        # find this mouse, overwrite everything from this mouse forward, after copying to a temp list 
        hasMouse = False
        # find this mouse
        filePos = statsFile.seek (49) # skip header
        for line in statsFile:
            mouseID, entries, entRewards, hFixes, hfRewards, resultDict = str(line).split ('\t')
            if int (mouseID) = self.tag:
                hasMouse = True
                break

        if hasMouse
            
                aMouse = Mouse (int (mouseID), int (entries), int (entRewards), int (hFixes), int (hfRewards), json.loads (resultDict))
                self.mouseArray.append(aMouse)
        except Exception as e:
            print ("Error writing updating stat file\n", str (e))


class Mice:
    """
    The mice class simply contains an array of mouse objects
    """
    def __init__(self, cageSettings):
        """
        Initializes the array of mice with mice from any existing quickStats file, or with empty arry of mice,if no quickStats file
        """
        self.mouseArray=[]
        # now look for quickstats file from today or yesterday
        now = datetime.fromtimestamp (time())
        dateStr= str (now.year) + (str (now.month)).zfill(2) + (str (now.day)).zfill(2)
        dayFolderPath = cageSettings.dataPath + dateStr + '/' + cageSettings.cageID + '/'
        textFilePath = dayFolderPath + 'TextFiles/quickStats_' + cageSettings.cageID + '_' +  dateStr + '.txt'
        hasStats = False
        if os.exists (textFilePath):
            hasStats = True
        else:
            # nothing from today, try yesterday
            yesterday = now - timedelta (hours=24)
            dateStr= str (yesterday.year) + (str (yesterday.month)).zfill(2) + (str (yesterday.day)).zfill(2)
            dayFolderPath = cageSettings.dataPath + dateStr + '/' + cageSettings.cageID + '/'
            textFilePath = dayFolderPath + 'TextFiles/quickStats_' + cageSettings.cageID + '_' +  dateStr + '.txt'
            if os.exists (textFilePath): # stats for yesterday
                hasStats = True
            else:
                haStats = False
        # open the file
        if hasStats:
            with open(textFilePath, 'r') as statsFile:
                statsFile.seek (49) # skip header
                for line in statsFile:
                    mouseID, entries, entRewards, hFixes, hfRewards, resultDict = str(line).split ('\t')
                    aMouse = Mouse (int (mouseID), int (entries), int (entRewards), int (hFixes), int (hfRewards), json.loads (resultDict))
                    self.mouseArray.append(aMouse)
                

    def addMouse (self, addMouse, statsFile):
        """
        Appends a mouse object to the array and updates quickstats file with new mouse
        :param aMouse: the mouse object to append
        :param statsfp: file pointer to the quickstats file so it can be updated
        """
        hasMouse = False
        for mouse in self.mouseArray:
            if mouse.tag == addMouse.tag:
                print ('Mouse with tag {:d} has already been added'.format (addMouse.tag))
                hasMouse = True
                break
        if not hasMouse:
            self.mouseArray.append(addMouse)
        # add a line to the quik stats file
        hasMouse = False
        statsFile.seek (49) # skip the header
        for line in statsFile:
            mouseID, entries, entRewards, hFixes, hfRewards, resultDict = str(line).split ('\t')
            if mouseID = addMouse.tag:
                hasMouse = True
                print ('Mouse with tag {:d} is already in stats file'.format (addMouse.tag))
                break
        if not hasMouse: # we are at end of the file, so append new mouse
            outPutStr = '{:013}\t{:05}\t{:05}\t{:05}\t{:05}\t{:s}'.format(addMouse.tag, 0, 0, 0, 0,'{}')
            statsFile.write (outPutStr)
       

    def addMiceFromFile(self, statsfp):
        """
        Adds mouse objects to the mice array, initialzing tagID and initial values for rewards from quickstats file

        If there is a problem with the quickstats file structure, the file is scrubbed and started over with 0 mice
        :param statsfp: file pointer to the quickstats file
        returns:nothing
        """
        statsfp.seek (49)
        aline = statsfp.readline()
        while aline:
            try:
                mouseID, entries, entRewards, hFixes, hfRewards = str(aline).split ('\t')
                aMouse = Mouse (int (mouseID), int (entries), int (entRewards), int (hFixes), int (hfRewards))
                self.addMouse(aMouse, statsfp)
                aline = statsfp.readline()
            except ValueError:
                statsfp.truncate (39)
                self.mouseArray = []
                aline = statsfp.readline()
                print ('Daily Quick Stats File overwritten.')
        return
            

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
    m1= Mouse (16, 0,0,0,0,)
    m2 = Mouse (17, 0,0,0,0)
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
