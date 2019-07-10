import json
from time import time, localtime
from datetime import datetime,timedelta
from os import path
class Mouse:
    """
    Class to hold information about each mouse, each mouse gets its own object
    """
    def __init__(self, tag, entries, entranceRewards, headFixes, resultsDict = {}):
        """
        Makes a new mouse object, initializing with RFID tag, entrance and reward info, and results dictionary

        :param tag: RFID tag of this mouse
        :param entries: number of entries mouse has made
        :param entranceRewards: number of entrance rewards mouse has been given
        :param headFixes: number of head fixes for this mouse
        :param resultsDict: dictionary of results from stimulator

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
         # find this mouse, then stop, while keeping track of file pos
        filePos = statsFile.seek (42) # skip header
        mouseFilePos = -1
        try:
            for line in statsFile:
                if len(line) > 2:
                    mouseID, entries, entRewards, hFixes, resultDict = line.rstrip('\n').split ('\t')
                    if int (mouseID) == self.tag:
                        mouseFilePos = filePos
                        break
                    filePos += len (line)
        except Exception as e:
            print ('error : {}'.format (e))
            
        # if mouse not found, add it with current  data at end of file
        if mouseFilePos == -1:
            statsFile.write (outPutStr)
        else:
            # store rest of lines of file in temp list
            lines = []
            for line in statsFile:
                lines.append (line)
            # write new stats for this mouse at saved position
            filePos = statsFile.seek (mouseFilePos)
            statsFile.write (outPutStr)
            # write saved lines back to file
            for line in lines:
                statsFile.write (line)
        statsFile.flush()

class Mice:
    """
    The mice class simply contains an array of mouse objects
    """
    def __init__(self, expSettings, cageSettings):
        """
        Initializes the array of mice with mice from any existing quickStats file, or with empty arry of mice,if no quickStats file
        """
        self.mouseArray=[]
        #  look for quickstats file from today
        textFilePath ='{:s}TextFiles/quickStats_{:s}_{:s}.txt'.format(expSettings.dayFolderPath, cageSettings.cageID, expSettings.dateStr)
        if path.exists (textFilePath):
            with open(textFilePath, 'r') as statsFile:
                statsFile.seek (41) # skip header
                for line in statsFile:
                    if len (line) > 2:
                        mouseID, entries, entRewards, hFixes, resultDict = line.rstrip('\n').split ('\t')
                        self.mouseArray.append(Mouse (int (mouseID), int (entries), int (entRewards), int (hFixes), json.loads (resultDict)))


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
        # add mouse to the quik stats file
        hasMouse = False
        #fPos = 42
        statsFile.seek (41) # skip the header
        try:
            for line in statsFile:
                if len (line) > 2:
                    mouseID, entries, entRewards, hFixes, resultDict = line.rstrip('\n').split ('\t')
                    if mouseID == addMouse.tag:
                        hasMouse = True
                        print ('Mouse with tag {:d} is already in stats file'.format (addMouse.tag))
        except Exception as e:
            print ('addMouse error: {}'.format (e))
        if not hasMouse: # we are at end of the file, so append new mouse
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
            

#for testing
if __name__ == '__main__':
    from AHF_CageSet import AHF_CageSet
    from AHF_Settings import AHF_Settings
    import __main1__
    
    cageSettings = AHF_CageSet ()
    expSettings = AHF_Settings()

    __main1__.makeDayFolderPath (expSettings, cageSettings)
    __main1__.makeQuickStatsFile (expSettings, cageSettings)
    mArray = Mice(expSettings, cageSettings)
    mArray.addMouse (Mouse (16, 0,0,0,{}), expSettings.statsFP)
    mArray.addMouse (Mouse (17, 0,0,0,{}), expSettings.statsFP)
    mArray.addMouse (Mouse (17, 0,0,0,{}), expSettings.statsFP)
    mArray.addMouse (Mouse (16, 0,0,0,{}), expSettings.statsFP)
    """
    
    tm = mArray.getMouseFromTag(17)
    tm.entries +=1
    tm.headFixes +=1
    tm.updateStats (expSettings.statsFP)
    #m2.updateStats (expSettings.statsFP)
    #mArray.show()

    mArray.addMouse (m1, expSettings.statsFP)
    
    mArray.show()
    mTemp = mArray.getMouseFromTag (17)
    mTemp.show()
    mTemp = mArray.getMouseFromTag (16)
    mTemp.entries +=1
    mTemp.headFixes +=1
    mArray.show()
    mArray.removeMouseByTag (17)
    mArray.show()
    """
