#! /usr/bin/python3
#-*-coding: utf-8 -*-
import abc
from abc import ABCMeta, abstractmethod
import os
import inspect
from collections import OrderedDict

# methods for classes and dictionaries


##################################################################################
# methods for getting class names and importing classes from a base class
##################################################################################


def Class_from_file(fileName):
    """
    Imports a module from a fileName (stripped of the .py) and returns the class
    
    Assumes the class is named the same as the module. 
    """
    module = __import__(fileName)
    return getattr(module, fileName)



def File_exists (nameTypeStr, nameStr, typeSuffix):
    """
    Returns true if a file with name 'AHF_' + nameTypeStr + '_' + nameStr + typeSuffix exists in current directory
    """
    findFile = 'AHF_' + nameTypeStr + '_' + nameStr + typeSuffix
    # try to find the file name in current directory and load it
    returnVal = False
    for f in os.listdir('.'):
        if f == findFile:
            returnVal =  True
            break
    return returnVal

def File_from_user (nameTypeStr, longName, typeSuffix):
    """
    Static method that trawls through current folder looking for python files matching nameTypeStr
    
    Allows user to choose from the list of files found. Files are recognized by names starting
    with 'AHF_' + nameTypeStr' + '_' and ending with '.py'
    Raises: FileNotFoundError if no nameStr class files found
    """
    iFile=0
    fileList = []
    startStr = 'AHF_' + nameTypeStr + '_'
    #print (os.listdir(os.curdir))
    for f in os.listdir(os.curdir):
        if f.startswith (startStr) and f.endswith (typeSuffix):
            f= f.rstrip(typeSuffix)
            try:
                moduleObj=__import__ (f)
                #print ('module=' + str (moduleObj))
                classObj = getattr(moduleObj, moduleObj.__name__)
                isAbstractClass =inspect.isabstract (classObj)
                if isAbstractClass == False:
                    fileList.append (f.lstrip(startStr) + ": " + classObj.about())
                    iFile += 1
            except Exception as e: # exception will be thrown if imported module imports non-existant modules, for instance
                print (e)
                continue     
    if iFile == 0:
        print ('Could not find any %s files in the current directory' % longName)
        raise FileNotFoundError
    else:
        if iFile == 1:
            ClassFile =  fileList[0]
            print ('Class file found: ' + ClassFile)
        else:
            inputStr = '\nEnter a number from 0 to {} to Choose a {} class:\n'.format((iFile -1), longName)
            ii=0
            for file in fileList:
                inputStr += str (ii) + ': ' + file + '\n'
                ii +=1
            inputStr += ':'
            ClassNum = -1
            while ClassNum < 0 or ClassNum > (iFile -1):
                ClassNum =  int(input (inputStr))
            ClassFile =  fileList[ClassNum]
        return startStr + ClassFile.split (':')[0]


########################################################################################################################
## methods for user editing of a dictionary of settings containing strings, integers, floats, lists, tuples, booleans, and dictionaries of those types
#########################################################################################################################
def Show_ordered_dict (objectDict, longName):
    """
    Dumps standard dictionary settings into an ordered dictionary, prints settings to screen in a numbered fashion from the ordered dictionary,
    making it easy to select a setting to change. Returns the ordered dictionary, used by edit_dict function
    """
    print ('*************** Current %s Settings *******************' % longName)
    showDict = OrderedDict()
    itemDict = {}
    nP = 0
    for key in objectDict :
        value = objectDict.get (key)
        showDict.update ({nP:{key: value}})
        nP += 1
    for ii in range (0, nP):
        itemDict.update (showDict [ii])
        kvp = itemDict.popitem()
        print(str (ii) +') ', kvp [0], ' = ', kvp [1])
    return showDict


def Edit_dict (anyDict, longName):
    """
    Edits values in a passed in dict, in a generic way, not having to know ahead of time the name and type of each setting
    Assumption is made that lists/tuples contain only strings, ints, or float types, and that all members of any list/tuple are same type
    """
    while True:
        orderedDict = AHF_show_ordered_dict (anyDict, longName)
        updatDict = {}
        inputStr = input ('Enter number of setting to edit, or -1 to exit:')
        try:
            inputNum = int (inputStr)
        except ValueError as e:
            print ('enter a NUMBER for setting, please: %s\n' % str(e))
            continue
        if inputNum < 0:
            break
        else:
            itemDict = orderedDict.get (inputNum)
            kvp = itemDict.popitem()
            itemKey = kvp [0]
            itemValue = kvp [1]
            if type (itemValue) is str:
                inputStr = input ('Enter a new text value for %s, currently %s:' % (itemKey, str (itemValue)))
                updatDict = {itemKey: inputStr}
            elif type (itemValue) is int:
                inputStr = input ('Enter a new integer value for %s, currently %s:' % (itemKey, str (itemValue)))
                updatDict = {itemKey: int (inputStr)}
            elif type (itemValue) is float:
                inputStr = input ('Enter a new floating point value for %s, currently %s:' % (itemKey, str (itemValue)))
                updatDict = {itemKey: float (inputStr)}
            elif type (itemValue) is tuple or itemValue is list:
                outputList = []
                if type (itemValue [0]) is str:
                    inputStr = input ('Enter a new comma separated list of strings for %s, currently %s:' % (itemKey, str (itemValue)))
                    outputList = list (inputStr.split(','))
                elif type (itemValue [0]) is int:
                    inputStr = input ('Enter a new comma separated list of integer values for %s, currently %s:' % (itemKey, str (itemValue)))
                    for string in inputStr.split(','):
                        try:
                            outputList.append (int (string))
                        except ValueError:
                            continue
                elif type (itemValue [0]) is float:
                    inputStr = input ('Enter a new comma separated list of floating point values for %s, currently %s:' % (itemKey, str (itemValue)))
                    for string in inputStr.split(','):
                        try:
                            outputList.append (float (string))
                        except ValueError:
                            continue
                if type (itemValue) is tuple:
                    updatDict = {itemKey: tuple (outputList)}
                else:
                    updatDict = {itemKey: outputList}
            elif type (itemValue) is bool:
                inputStr = input ('%s, True for or False?, currently %s:' % (itemKey, str (itemValue)))
                if inputStr [0] == 'T' or inputStr [0] == 't':
                    updatDict = {itemKey: True}
                else:
                    updatDict = {itemKey: False}
            elif type (itemValue) is dict:
                AHF_edit_dict (itemValue, itemKey)
                anyDict[itemKey].update (itemValue)
            anyDict.update (updatDict)


def Obj_fields_to_dict(anObject):
    """
    Returns a dictionary with elements from the fields of the object anObject
    """
    aDict = {}
    for key, value in anObject.__dict__ :
        if key.startswith ('_') is False and inspect.isroutine (getattr (anObject, key)) is False:
            aDict.update({key: value})
    return aDict


def Dict_to_obj_fields (anObject, aDict):
    """
    Sets attributes for the object anObject from the keys and values of dictionay aDict
    """
    for key, value in aDict:
        setattr (anObject, key, value)


        
def Obj_fields_to_file (anObject, nameTypeStr, nameStr, typeSuffix):
    """
    Writes a file containing a json dictionary of all the fields of the object anObject
    """
    jsonDict = {}
    for key, value in anObject.__dict__ :
        if key.startswith ('_') is False and inspect.isroutine (getattr (anObject, key)) is False:
            jsonDict.update({key: value})
    configFile = 'AHF_' + nameTypeStr + '_' + nameStr + typeSuffix
    with open (configFile, 'w') as fp:
        fp.write (json.dumps (jsonDict, ":", separators = '\n'))
        fp.close ()
        uid = pwd.getpwnam ('pi').pw_uid
        gid = grp.getgrnam ('pi').gr_gid
        os.chown (configFile, uid, gid) # we may run as root for pi PWM, so we need to expicitly set ownership


        
def File_to_obj_fields (nameTypeStr, nameStr, longName, typeSuffix, anObject):
    """
    Sets attributes for the object anObject from the keys and values of dictionay aDict loaded from the file
    """
    filename = 'AHF_' + nameTypeStr + '_' + nameStr + typeSuffix
    errFlag = False
    with open (filename, 'r') as fp:
        data = fp.read()
        data=data.replace('\n', ',')
        configDict = json.loads(data)
        fp.close()
    for key, value in configDict:
        try:
            setattr (anObject, key, value)
        except ValueError:
            errFlag = True
    if errFlag:
        raise ValueError
