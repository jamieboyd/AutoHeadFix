#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from AHF_Base import AHF_Base

class AHF_Mice (AHF_Base, metaclass = ABCMeta):
    """
    Base class for mice. Contains an array of Mouse objects, plus a reference to the Task object
    Additionally, Mouse objects may have appended attributes as follows:
    Dictionaries from Stimulator, 1 for results, stimResults, and 1 for parameters, stimParams
    Dictionary from HeadFixer, either headFix% or headFix type (loose, strong, a scale from 1 -8)
    Dictionary from Rewarder, task and entry reward size, max entry rewards, daily reward totals
    """


from AHF_Task import Task
import AHF_ClassAndDictUtils as CAD
from AHF_TagReader import AHF_TagReader
from AHF_Base import AHF_Base

