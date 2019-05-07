#! /usr/bin/python3
#-*-coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import os
import inspect
from AHF_Base import AHF_Base

class AHF_Camera(AHF_Base, metaclass = ABCMeta):
    """
    AHF_Camera is the base class for the main brain imaging camera used in Auto Head Fix
    """

if __name__ == '__main__':
    import time
    import PTSimpleGPIO
    from PTSimpleGPIO import PTSimpleGPIO, Pulse, Train, Infinite_train

    t1 = Train (PTSimpleGPIO.INIT_FREQ, 14.4, 0.5, 30, 17, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)

    videoFormat = 'rgb'
    quality = 0
    resolution = (256,256)
    frameRate = 30
    iso = 0
    whiteBalance = True
    previewWin =(0,0,256,256)
    #userDict = AHF_Camera.dict_from_user ({})
    #camera=AHF_Camera (userDict)
    camera=AHF_Camera ({'format': videoFormat, 'quality' : quality, 'resolution' : resolution, 'iso' : iso, 'whiteBalance': whiteBalance, 'previewWin' :(0,0,320, 240)})
    videoPath = '/home/pi/lolcat.' + camera.AHFvideoFormat
    t1.do_train()
    camera.start_recording(videoPath)
    sleep (1.5)
    print ('Recording 5 sec video')
    frameNow = camera.frame
    frameIndex = frameNow.index
    frameStop = 500
    frameOld = 0
    indexOld=0
    frameNow_array = []
    frameIndex_array = []
    time_start = time.time()
    while camera.frame.index < frameStop:
        #frameNow = camera.frame
        frameIndex = camera.frame.index
        #print (frameNow.index)
        #frameNow = camera.frame
        #frameIndex = frameNow.index
        #print (frameNow.timestamp, frameIndex)
        if frameIndex == indexOld: continue
        frameNow_array.append(camera.frame.timestamp)
        frameIndex_array.append(camera.frame.index)
        indexOld = frameIndex
        #sleep (0.01)
    time_end=time.time()

    previous_frame = 0
    total_time = 0
    for k in range(len(frameNow_array)-1):
        #if frameIndex_array[k] == previous_frame: continue

        #previous_frame = frameIndex_array[k]
        if (frameNow_array[k+1] is None) or (frameNow_array[k] is None):
            print (frameIndex_array[k], frameNow_array[k-1], frameNow_array[k], frameNow_array[k+1])
            continue

        print (frameIndex_array[k], 1E6/(frameNow_array[k+1]-frameNow_array[k]))

        total_time +=(frameNow_array[k+1]-frameNow_array[k])*1E-6

    print (time_start, time_end, time_end-time_start)
    print (total_time)

    #class picamera.PiVideoFrame(index, frame_type, frame_size, video_size, split_size, timestamp)

    camera.stop_recording()
    #camera.adjust_config_from_user ()
    #videoPath = '/home/pi/Documents/testMod.' + camera.AHFvideoFormat
    #print ('About to record a 5 sec timed video')
    #camera.timed_recording(videoPath, 5.0)
