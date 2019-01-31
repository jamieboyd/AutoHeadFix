#! /usr/bin/python
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class AHF_TagReader (metaclass = ABCMeta):

    @staticmethod
    def about ():
        return 'about message for this RFID-Tag Reader class goes here'

    
    @staticmethod
    @abstractmethod
    def config_user_get (starterDict = {}):
        return {}


    @abstractmethod
    def __init__ (self, RFIDdict):
        pass

    @abstractmethod
    def setup (self):
        pass

    @abstractmethod
    def readTag (self):
        pass

    @abstractmethod
    def hardwareTest (self):
        pass
