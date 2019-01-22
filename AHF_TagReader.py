#! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

class AHF_TagReader (metaclass = ABCMeta):

    globalTag = 0
        
    @staticmethod
    def about ():
        return 'about message for this RFID-Tag Reader class goes here'

    
    @staticmethod
    @abstractmethod
    def config_user_get ():
        return {}


    @abstractmethod
    def __init__ (self, RFIDdict):
        pass

    @abstractmethod
    def setup (self):
        pass

     @abstractmethod
    def clearBuffer (self):
        """
        Clears the serial inout buffer for the serialport used by the tagReader
        """
        pass

    @abstractmethod
    def readTag (self):
        pass


    @abstractmethod
    def checkSum(self, tag, checkSum):
        pass

    @abstractmethod
    def installCallBack (self):


    @abstractmethod
    def hardwareTest (self):
        pass
