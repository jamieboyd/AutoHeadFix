#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Camera import AHF_Camera
from picamera import PiCamera
from time import sleep

class AHF_Camera_PiCam (AHF_Camera):

    @staticmethod
    def about ():
        return 'uses picamera.PiCamera to run the standard Raspberry Pi camera'

    def config_user_get ():
        paramDict = {}
        # resolution
        resolution = paramDict.get ('resolution', (640, 480))
        tempInput = input ('set X,Y resolution (currently ' + str (resolution) + ') to :')
        if tempInput != '':
            resolution = tuple (int(x) for x in tempInput.split (','))
        paramDict.update ({'resolution' : resolution})
        # framerate
        frameRate = paramDict.get ('framerate', 30)
        tempInput = input ('Set Frame rate in Hz of recorded movie (currently ' + str (frameRate) + ') to :')
        if tempInput != '':
            frameRate = float (tempInput)
        paramDict.update ({'framerate' : frameRate})
        # ISO
        iso = paramDict.get ('iso', 200)
        tempInput = input ('Set ISO for video, or 0 to auto set gains (currently ' + str (iso) + ') to :')
        if tempInput != '':
            iso = int (tempInput)
        paramDict.update ({'iso' : iso})
        # shutter speed
        shutter_speed = paramDict.get ('shutter_speed', 30000)
        tempInput = input ('Set Shutter speed (in microseconds) for recorded video (currently ' + str (shutter_speed) + ') to :')
        if tempInput != '':
            shutter_speed= int (tempInput)
        paramDict.update ({'shutter_speed' : shutter_speed})
        # videoFormat
        videoFormat = paramDict.get ('format', 'h264' )
        tempInput = input ('Set Video format for recording movies (currently ' + videoFormat + ') to :')
        if tempInput != '':
            videoFormat = tempInput
        paramDict.update ({'format' : videoFormat})
        # quality
        quality = paramDict.get ('quality', 20)
        tempInput = input ('Set Video quality for h264 movies, best=1, worst =40,0 for auto (currently ' + str (quality) + ') to :')
        if tempInput != '':
            quality = int (tempInput)
        paramDict.update ({'quality' : quality})
        # preview window
        previewWin = paramDict.get ('previewWin', (0,0,640,480))
        tempInput = input ('Set video preview window, left, top, right, bottom, (currently ' + str(previewWin) + ') to :')
        if tempInput != '':
            previewWin = tuple (int(x) for x in tempInput.split (','))
        paramDict.update ({'previewWin' : previewWin})
        # white balance
        whiteBalance = paramDict.get ('whiteBalance', False)
        tempInput = input ('Set white balancing for video, 1 for True, or 0 for Flase (currently ' + str (whiteBalance) + ') to :')
        if tempInput !='':
            tempInput = bool (int (tempInput))
        paramDict.update ({'whiteBalance' : whiteBalance})
        # return already modified dictionary, needed when making a new dictionary
        return paramDict


        
    def __init__(self, paramDict):
        """
        Initializes an AHF_Camera object from a dictonary and sets the gain as appropriate

        :param paramDict.format: video format for recording, default='.h264'
        :param paramDict.quality: different video formats interpret quality paramater differently, default = 10
        :param paramDict.resolution: two-tuple of horizontal pixel number and vertical pixel number default= (640, 480)
        :param paramDict.framerate: rate,1 in Hz, at which to record video, default = 30
        :param paramDict.shutter_speed: camera exposure time, in microseconds, inverse must be less than frame rate default = 30
        :param paramDict.iso: used to set gain of camera directly, or use 0 to have camera calculate gain from a preview
        :param paramDict.whiteBalance: set to True if you want camera to auto white balance, set to False to set all color gains to 1, default = False
        :param paramDict.previewWin: set the size of the preview window, in pixels a tuple of (left, top, right, bottom) coordinates. default = (0,0,640,480)
        :raises PiCameraError: error raised by superclass PiCamera if camera is not found, or can't be initialized
        """
        self.paramDict = paramDict
        # init PiCamera
        self.setup()

    def setup (self):
        try:
            self.piCam = PiCamera()
        except Exception as anError:
            print ("Error initializing camera.." + str (anError))
            raise anError
        # set fields in Picamera
        self.piCam.resolution = paramDict.get ('resolution', (640, 480))
        self.piCam.framerate = paramDict.get ('framerate', 30)
        self.piCam.iso = paramDict.get ('iso', 0)
        self.piCam.shutter_speed = paramDict.get ('shutter_speed', 30000)
        # set fields that are in AHF_Camera class
        self.AHFvideoFormat = paramDict.get ('format', 'h264')
        self.piCam.AHFvideoQuality = paramDict.get ('quality', 20)
        self.piCam.AHFframerate= paramDict.get ('framerate', 30)
        self.piCam.AHFpreview = paramDict.get('previewWin', (0,0,640,480))
        whiteBalance = paramDict.get ('whiteBalance', False)
        self.piCam.AHFgainMode = (whiteBalance == True) # set bit 0 of gain for auto white balancing
        self.piCam.AHFgainMode += 2 * (self.iso == 0) # set bit 1 for auto gain
        # turn off LED on camera
        self.piCam.led = False
        # set gain based on 2 sec preview
        self.set_gain ()
        return

    def get_configDict (self):
        """
        Loads camera settings into a dictionary with same keys as used in __init__ and returns that dictionary

        Note that we use float () on framerate becuase it is a Fraction, i,e, 30 is represented as Fraction (30, 1)
        and it doen't serialize for storing as a JSON dict
        """
        paramDict = {'resolution' : self.resolution, 'framerate' : float (self.framerate), 'iso' : self.iso}
        paramDict.update ({'shutter_speed' : self.shutter_speed, 'format' : self.AHFvideoFormat})
        paramDict.update ({'quality' : self.AHFvideoQuality, 'framerate' : self.AHFframerate})
        paramDict.update ({'previewWin' : self.AHFpreview, 'whiteBalance' : bool(self.AHFgainMode & 1)})
        return paramDict

    def set_params (self, paramDict):
        """
        modifies paramaters for an AHF_Camera object from a dictonary

        :param paramDict: dictionary of setings to change, same format as for __init__()
        """

        # set fields in  super-class
        if 'resolution' in paramDict:
            self.resolution = paramDict ['resolution']
        if 'framerate' in paramDict:
            self.framerate = paramDict ['framerate']
        if 'iso' in paramDict:
            self.iso = paramDict ['iso']
            if self.iso == 0 and (self.AHFgainMode & 2) == 0:
                self.AHFgainMode = self.AHFgainMode | 2  # set bit 1 for auto gain
            elif self.iso != 0 and (self.AHFgainMode & 2) == 2:
                self.AHFgainMode -= 2 # unset bit 1 for auto gain
        if 'shutter_speed' in paramDict:
            self.shutter_speed = paramDict ['shutter_speed']
        # set fields that are in AFF_Camera class
        if 'format' in paramDict:
            self.AHFvideoFormat = str (paramDict ['format'])
        if 'quality' in paramDict:
            self.AHFvideoQuality = int (paramDict ['quality'])
        if 'framerate' in paramDict:
            self.AHFframerate= paramDict ['framerate']
        if 'previewWin' in paramDict:
            self.AHFpreview = paramDict['previewWin']
        if 'whiteBalance' in paramDict:
            if paramDict ['whiteBalance'] == True and (self.AHFgainMode & 1) == 0:
                self.AHFgainMode = self.AHFgainMode | 1 # set bit 0 of gain for auto white balancing
            elif paramDict ['whiteBalance'] == False and (self.AHFgainMode & 1) == 1:
                self.AHFgainMode -= 1 # unset bit 0 of gain for auto white balancing
        return


    def show_config (self):
        """
        prints the settings for the camera
        """
        print ('----------------Current Settings for AHFCamera----------------')
        print ('1:Video resolution = ' + str (self.resolution))
        print ('2:Video Frame Rate = ' + str(self.framerate))
        print ('3:Camera ISO = ' + str (self.iso) + '; Do Auto-Gain = ' + str (bool(self.AHFgainMode & 2)))
        print ('4:Shutter Speed (in microseconds) = ' + str (self.shutter_speed))
        print ('5:Video Format = ' + self.AHFvideoFormat)
        print ('6:Video Quality =' + str (self.AHFvideoQuality))
        print ('7:Frame Rate = ' + str (self.AHFframerate))
        print ('8:Preview Window = ' + str (self.AHFpreview))
        print ('9:White Balancing =' + str (bool(self.AHFgainMode & 1)))
        return


    def adjust_config_from_user (self):
        """
        Lets the user change the settings for the camera
        :returns: a dictionary containing the new, modified  version fo the settings
        """
        while True:
            try:
                self.show_config()
                print ('10:Run Auto-Gain Now')
                event = int (input ('Enter number of paramater to Edit, or 0 when done:'))
            except ValueError:
                continue
            if event == 1:
               self.resolution = tuple (int(x) for x in input('X/Y resolution for video, e.g. 640, 480:').split (','))
            elif event == 2:
                self.framerate = float (input ('Frame rate in Hz of recorded movie:'))
            elif event == 3:
                self.iso= int (input ('ISO for video, or 0 to auto set gains:'))
                if self.iso == 0 and (self.AHFgainMode & 2) == 0:
                    self.AHFgainMode = self.AHFgainMode | 2  # set bit 1 for auto gain
                elif self.iso != 0 and (self.AHFgainMode & 2) == 2:
                    self.AHFgainMode -= 2 # unset bit 1 for auto gain
            elif event == 4:
               self.shutter_speed = int (input ('Shutter speed (in microseconds) for recorded video:'))
            elif event == 5:
               self.AHFvideoFormat = str (input ('Video format for recording movies, e.g. h264 or rgb:'))
            elif event == 6:
               self.AHFvideoQuality = int (input ('Video quality for h264 movies (best=1, worst =40,0 for auto, not used for rgb format):'))
            elif event == 7:
               self.AHFframerate = float (input ('Frame rate in Hz of recorded movie:'))
            elif event == 8:
               self.AHFpreview = tuple (int(x) for x in input ('video preview window, a tuple (left, top, right, bottom):').split (','))
            elif event == 9:
                tempVal =  bool(int (input('Do white balance for video (1 for yes, or 0 for no:')))
                if tempVal == True and (self.AHFgainMode & 1) == 0:
                    self.AHFgainMode = self.AHFgainMode | 1 # set bit 0 of gain for auto white balancing
                elif tempVal == False and (self.AHFgainMode & 1) == 1:
                    self.AHFgainMode -= 1 # unset bit 0 of gain for auto white balancing
            elif event == 10:
               self.set_gain()
            elif event == 0:
               break
            else:
               print ('Enter a number from 0 to 10')
        return self.get_configDict ()


    def set_gain (self):
        """
        Sets the gain and white balance of the camera based on a 2 second preview - so set illumination as you like before calling

        If ISO for the camera is set to non-zero value, gain is not settable. If pWhiteBalance was set to False, white balancing is not done,
        and gains for red and green are set to 1.
        :raises PiCameraError: error raised by superclass PiCamera from preview
        """
        DescStr = 'Setting Gain for AHF_Camera '
        if (self.AHFgainMode & 2):
            DescStr += 'from current illumination'
        else:
            DescStr += "from ISO " + str (self.iso)
        if (self.AHFgainMode & 1):
            DescStr += ' with white balancing'
        else:
            DescStr += " with No white balancing"
        print (DescStr)
        if (self.AHFgainMode & 1):
            self.awb_mode='auto'
        else:
            self.awb_mode='off'
            self.awb_gains = (1,1)
        #if (self.AHFgainMode & 2):
        self.exposure_mode = 'auto'
        #else:
        #    self.exposure_mode = 'off'
        super().start_preview(fullscreen = False, window=self.AHFpreview)
        sleep(2.0) # let gains settle, then fix values
        if (self.AHFgainMode & 1):
            savedGain = self.awb_gains
            self.awb_gains = savedGain
            self.awb_mode = "off"
        #if (self.AHFgainMode & 2):
        self.exposure_mode = 'off'
        super().stop_preview ()
        print ("Red Gain for white balance =" + str (float(self.awb_gains [0])))
        print ("Blue Gain for white balance =" + str (float(self.awb_gains [1])))
        print ("Analog Gain = " + str(float (self.analog_gain)))
        print ("Digital Gain = " + str (float(self.digital_gain)))
        return

    def start_recording(self, video_name_path):
        """
        Starts a video recording using the saved settings for format, quality, gain, etc.

        A preview of the recording is always shown

        :param video_name_path: a full path to the file where the video will be stored. Always save to a file, not a PIL, for, example
        """
        if self.AHFvideoFormat == 'rgb':
            super().start_recording(output=video_name_path, format=self.AHFvideoFormat)
        else:
            super().start_recording(video_name_path, format = self.AHFvideoFormat, quality = self.AHFvideoQuality)
        super().start_preview(fullscreen = False, window= self.AHFpreview)

        return

    def stop_recording(self):
        """
        Stops a video recording previously started with start_recording.
        """
        if self.recording:
            super().stop_recording()
            super().stop_preview()
        return

    def timed_recording(self, video_name_path, recTime):
        """
        Does a timed video recording using the PiCamera wait_recording function.

        A preview of the recording is always shown

        Control does not pass back to the calling function until the recording is finished
        :param  video_name_path: a full path to the file where the video will be stored.
        :param recTime: duration of the recorded video, in seconds
        """
        if self.AHFvideoFormat == 'rgb':
            super().start_recording(output=video_name_path, format=self.AHFvideoFormat)
        else:
            super().start_recording(output=video_name_path, format=self.AHFvideoFormat)
        super().start_preview(fullscreen = False, window= self.AHFpreview)
        super().wait_recording(timeout=recTime)
        self.stop_recording ()
        return

    def __del__(self):
        super().close()


    @staticmethod
    def dict_from_user (paramDict):
        """
            static method that leys user make or edit a dictionary object that holds camera setttings
        
            configure gets info from user with the input function, which returns strings
        """
        if paramDict is None:
            paramDict = {}
        # resolution
        resolution = paramDict.get ('resolution', (640, 480))
        tempInput = input ('set X,Y resolution (currently ' + str (resolution) + ') to :')
        if tempInput != '':
            resolution = tuple (int(x) for x in tempInput.split (','))
        paramDict.update ({'resolution' : resolution})
        # framerate
        frameRate = paramDict.get ('framerate', 30)
        tempInput = input ('Set Frame rate in Hz of recorded movie (currently ' + str (frameRate) + ') to :')
        if tempInput != '':
            frameRate = float (tempInput)
        paramDict.update ({'framerate' : frameRate})
        # ISO
        iso = paramDict.get ('iso', 0)
        tempInput = input ('Set ISO for video, or 0 to auto set gains (currently ' + str (iso) + ') to :')
        if tempInput != '':
            iso = int (tempInput)
        paramDict.update ({'iso' : iso})
        # shutter speed
        shutter_speed = paramDict.get ('shutter_speed', 30000)
        tempInput = input ('Set Shutter speed (in microseconds) for recorded video (currently ' + str (shutter_speed) + ') to :')
        if tempInput != '':
            shutter_speed= int (tempInput)
        paramDict.update ({'shutter_speed' : shutter_speed})
        # videoFormat
        videoFormat = paramDict.get ('format', 'h264' )
        tempInput = input ('Set Video format for recording movies (currently ' + videoFormat + ') to :')
        if tempInput != '':
            videoFormat = tempInput
        paramDict.update ({'format' : videoFormat})
        # quality
        quality = paramDict.get ('quality', 20)
        tempInput = input ('Set Video quality for h264 movies, best=1, worst =40,0 for auto (currently ' + str (quality) + ') to :')
        if tempInput != '':
            quality = int (tempInput)
        paramDict.update ({'quality' : quality})
        # preview window
        previewWin = paramDict.get ('previewWin', (0,0,640,480))
        tempInput = input ('Set video preview window, left, top, right, bottom, (currently ' + str(previewWin) + ') to :')
        if tempInput != '':
            previewWin = tuple (int(x) for x in tempInput.split (','))
        paramDict.update ({'previewWin' : previewWin})
        # white balance
        whiteBalance = paramDict.get ('whiteBalance', False)
        tempInput = input ('Set white balancing for video, 1 for True, or 0 for Flase (currently ' + str (whiteBalance) + ') to :')
        if tempInput !='':
            tempInput = bool (int (tempInput))
        paramDict.update ({'whiteBalance' : whiteBalance})
        # return already modified dictionary, needed when making a new dictionary
        return paramDict


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
