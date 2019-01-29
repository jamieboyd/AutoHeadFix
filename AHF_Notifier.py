#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect

class AHF_Notifier (metaclass = ABCMeta):
    """
    Some remote way of notifying somebody, with email or text or something.
    """
    @staticmethod
    @abstractmethod
    def about ():
        return 'Message for your notifier class goes here.'

    @staticmethod
    @abstractmethod
    def config_user_get():
        return {}

    @abstractmethod
    def __init__ (self, NotifierDict):
        """Makes a new AHF_Notifier object
        
        return: nothing
        """
        pass


    @abstractmethod
    def notify (self, tag, durationSecs, isStuck):
        """
        Sends a text message with the given information.

        Two types of message can be sent, depending if isStuck is True or False
        No timing is done by the AHF_Notifier class, the durations are only for building the text mssg
        :param tag: RFID tag of the mouse
        :param durationSecs: how long the mouse has been inside the chamber
        :param isStuck: boolean signifying if the mouse has been inside the chamber for too long, or has just left the chamber
        :return: nothing
        """

        



if __name__ == '__main__':
    import requests
    notifier=AHF_Notifier(18, (17789535102, 16043512437,16047904623), 'c67968bac99c6c6a5ab4d0007efa6b876b54e228IoOQ7gTnT6hAJDRKPnt6Cwc9b')
    notifier.notify (44, 60, 0)

    
