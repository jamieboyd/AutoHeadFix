import json
from time import time, localtime
from datetime import datetime,timedelta
from os import path
class Mouse:
    """
    Each mouse is a Mouse object with fields for tag, entries, entrance rewards, head fixes, and a dictionary for stimulator to use
    
    """
    def __init__(self, tag, entries, entranceRewards, headFixes, resultsDict = {}):
        """
        Makes a new mouse object, initializing with RFID tag, entrance and reward info, and results dictionary

        :param tag: RFID tag of this mouse
        :param entries: number of entries mouse has made
        :param entranceRewards: number of entrance rewards mouse has been given
        :param headFixes: number of head fixes for this mouse
        :param resultsDict: dictionary of results and or settings from stimulator, default is empty dictionary

        """
        self.tag = tag
        self.entries = entries
        self.entranceRewards = entranceRewards
        self.headFixes = headFixes
        self.stimResultsDict = resultsDict

    def clear (self):
        """
        Clears the stats for entries and rewards for this mouse, done at the start of every day
        stimulator may clear resultsDict at beginning of day as well
        """
        self.entries = 0
        self.headFixes = 0
        self.entranceRewards = 0

    def show (self):
        """
        Prints to the shell all the data for this mouse, including any stimResults info
        """
        print ('MouseID:{:013d}\tEntries:{:05d}\tHeadFixes:{:05d}\tEntry Rewards:{:05d}'.format (self.tag, self.entries, self.headFixes, self.entranceRewards))
        if self.stimResultsDict is not None:
            stimResults = 'Stim Results:'
            for key in self.stimResultsDict:
                stimResults += '\t' + key + " = " + str (self.stimResultsDict.get (key))
            print (stimResults)


    def updateStats (self, statsFile):
        """
        Updates the quick stats text file after every exit, mostly for the benefit of folks logged in remotely, but also to save state in case program is restarted
        :param statsFile: file pointer to the stats file
        returns:nothing
        """
        # make line to insert in file with data from this mouse
        outPutStr = '{:013}\t{:05}\t{:05}\t{:05}\t{:s}\n'.format(self.tag, self.entries, self.entranceRewards, self.headFixes, json.dumps(self.stimResultsDict))
        # find this mouse, then stop
        mPos = statsFile.seek (42) # skip header, including new line
        aLine = statsFile.readline()
        while len (aLine) > 2:
            mouseID, entries, entRewards, hFixes, resultDict = aLine.rstrip('\n').split ('\t')
            if int (mouseID) == self.tag:
                break
            mPos = statsFile.tell()
            aLine = statsFile.readline()
        # store any remaining lines of file in temp list
        tempLines = []
        aLine = statsFile.readline()
        while len (aLine) > 2:
            tempLines.append(aLine)
            aLine = statsFile.readline()
        # write new stats for this mouse at saved position
        statsFile.seek (mPos)
        statsFile.write(outPutStr)
        # write saved lines back to file, this will leave file pos at end of file
        for aLine in tempLines:
            statsFile.write (aLine)
        statsFile.flush()


class Mice:
    """
    The mice class simply contains an array of mouse objects 
    """
    def __init__(self, statsFile):
        """
        Initializes the array of mice with mice from any existing quickStats file, or with empty arry of mice,if no quickStats file
        :param statsFile: stats file, which  may be frshly made and blank
        """
        self.mouseArray=[]
        statsFile.seek (42) # skip header
        aLine = statsFile.readline()
        while len (aLine) > 2:
            mouseID, entries, entRewards, hFixes, resultDict = line.rstrip('\n').split ('\t')
            self.mouseArray.append(Mouse (int (mouseID), int (entries), int (entRewards), int (hFixes), json.loads (resultDict)))
            aLine = statsFile.readline()

    def addMouse (self, addMouse, statsFile):
        """
        Appends a mouse object to the array and updates quickstats file with new mouse
        :param aMouse: the mouse object to append
        :param statsfp: file pointer to the quickstats file so it can be updated
        """
        hasMouse = False
        for mouse in self.mouseArray:
            if mouse.tag == addMouse.tag:
                print ('Mouse with tag {:d} has already been added to mice array'.format (addMouse.tag))
                hasMouse = True
                break
        if not hasMouse:
            self.mouseArray.append(addMouse)
            self.mouseArray.sort()
        # add mouse to the quik stats file
        hasMouse = False
        mPos = statsFile.seek (42) # skip the header
        aLine = statsFile.readline()
        while len (aLine) > 2:
            mouseID, entries, entRewards, hFixes, resultDict = aLine.rstrip('\n').split ('\t')
            if mouseID == addMouse.tag:
                hasMouse = True
                break
            aLine = statsFile.readline()
        # put file pointer to end of file, good practive whether adding a mouse or not
        statsFile.seek(0, 2)
        if not hasMouse: # append new mouse
            outPutStr = '{:013d}\t{:05d}\t{:05d}\t{:05d}\t{:s}\n'.format(addMouse.tag, addMouse.entries, addMouse.entranceRewards, addMouse.headFixes, json.dumps(addMouse.stimResultsDict))
            statsFile.write (outPutStr)
            statsFile.flush()

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

    def nMice(self):
        """
        gets the number of mice in the mouse array
        :returns: the number of mice in the array
        """
        return len (self.mouseArray)


    def generator(self):
        """
        A Generator function that generates each of the mice in turn.
        Sample function call: for mouse in myMice.generator():
        """
        for mouse in self.mouseArray:
            yield mouse
            
