#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_Notifier(AHF_Base, metaclass = ABCMeta):
    """
    Some remote way of notifying somebody, with email or text or something.
    """


    @abstractmethod
    def notifyStuck(self, tag, cageID, duration, isStuck):
        """
        Sends a text message with the given information.

        Two types of message can be sent, depending if isStuck is True or False
        No timing is done by the AHF_Notifier class, the durations are only for building the text mssg
        :param tag: RFID tag of the mouse
        :param cageID: cage ID of the mouse that is stuck
        :param durationSecs: how long the mouse has been inside the chamber
        :param isStuck: boolean signifying if the mouse has been inside the chamber for too long, or has just left the chamber
        :return: nothing
        """
        pass


    @abstractmethod
    def notify(self, msgStr):
        """
        a more general method to send text information
        """
        pass

    def hardwareTest(self):
        msgStr = 'This is a test of the AHF_Notifer system using ' + self.__class__.__name__
        try:
            self.notify(msgStr)
        except exception as e:
            print('An error occurred:' + str(e))
        response = input('Do you wish to change Notifier settings? ')
        if response [0] =='Y' or response [0] == 'y':
            self.settingsDict = self.config_user_get(self.settingsDict)
