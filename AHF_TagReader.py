#! /usr/bin/python
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base
class AHF_TagReader (AHF_Base, metaclass = ABCMeta):

    @abstractmethod
    def readTag (self):
        pass
