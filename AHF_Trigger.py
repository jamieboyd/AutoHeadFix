#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect

class AHF_Trigger(metaclass = ABCMeta):
    """
    Sends/receives signals as to another pi to start/stop recording

    """
    @staticmethod
    @abstractmethod
    def about():
        return 'description of your trigger class goes here.'

    
    @staticmethod
    @abstractmethod
    def config_user_get ():
        return {}

    @abstractmethod
    def __init__ (self, UDPdict):
        pass

    @abstractmethod
    def doTrigger (self, message):
       pass

    @abstractmethod
    def getTrigger (self):
        pass
