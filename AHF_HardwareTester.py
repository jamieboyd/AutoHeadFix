#! /usr/bin/python3
#-*-coding: utf-8 -*-

from collections import OrderedDict
import inspect
from AHF_Task import Task
from AHF_Base import AHF_Base

def Show_testable_objects (anObject):
    print ('\n*************** Testable Auto Head Fix Objects *******************')
    showDict = OrderedDict()
    itemDict = {}
    nP = 0
    fields = sorted (inspect.getmembers (anObject))
    for item in fields:
       if isinstance(item[1], AHF_Base) and hasattr (item[1], 'hardwareTest'):
            showDict.update ({nP:{item [0]: item [1]}})
            nP +=1
    # print to screen 
    for ii in range (0, nP):
        itemDict.update (showDict.get (ii))
        kvp = itemDict.popitem()
        print(str (ii + 1) +') ', kvp [0], ' = ', kvp [1])
    print ('**********************************\n')
    return showDict


if __name__ == '__main__':
    def hardwareTester ():
        """
        Hardware Tester for Auto Head Fixing, allows you to verify the various hardware bits are working
        """
        # when run as __main__, user chooses exp config file
        task = Task('')
        task.setup ()
        # now that hardware is initialized, enter hardware test loop
        htloop (task)
else:
    def hardwareTester (task):
        """
        Hardware Tester for Auto Head Fixing, allows you to verify the various hardware bits are working
        """
        htloop (task)

def htloop (task):
    while True:
        showDict = Show_testable_objects (task)
        inputStr = input ('Enter number of object to test, or 0 to exit:')
        try:
            inputNum = int (inputStr)
        except ValueError as e:
            print ('enter a NUMBER for testing, please: %s\n' % str(e))
            continue
        if inputNum == 0:
            break
        else:
            itemDict = {}
            itemDict.update (showDict [inputNum -1]) #itemDict = OrderedDict.get (inputNum -1)
            kvp = itemDict.popitem()
            itemValue = kvp [1]
            itemValue.hardwareTest ()

if __name__ == '__main__':
    hardwareTester()
