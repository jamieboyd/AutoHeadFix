#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AHF_Camera import AHF_Camera
from picamera import PiCamera
from time import sleep

class AHF_Camera_PiCam (AHF_Camera):

    @staticmethod
    def about ():
        return 'uses picamera.PiCamera to run the standard Raspberry Pi camera'

    @staticmethod
    def config_user_get (starterDict = {}):
        defaultRes = (640,480)
        defaultFrameRate = 30
        defaultISO = 200
        defaultShutterSpeed = 30000
        defaultFormat = 'rgb'
        defaultQuality = 20
        # resolution
        resolution = starterDict.get ('resolution', defaultRes)
        tempInput = input ('set X,Y resolution (currently {0}): '.format(resolution))
        if tempInput != '':
            resolution = tuple (int(x) for x in tempInput.split (','))
        starterDict.update ({'resolution' : resolution})
        # framerate
        frameRate = starterDict.get ('framerate', 30)
        tempInput = input ('Set Frame rate in Hz of recorded movie (currently  {0}): '.format (frameRate))
        if tempInput != '':
            frameRate = float (tempInput)
        starterDict.update ({'framerate' : frameRate})
        # ISO
        iso = starterDict.get ('iso', 200)
        tempInput = input ('Set ISO for video, or 0 to auto set gains (currently ' + str (iso) + ') to :')
        if tempInput != '':
            iso = int (tempInput)
        starterDict.update ({'iso' : iso})
        # shutter speed
        shutter_speed = starterDict.get ('shutter_speed', 30000)
        tempInput = input ('Set Shutter speed (in microseconds) for recorded video (currently ' + str (shutter_speed) + ') to :')
        if tempInput != '':
            shutter_speed= int (tempInput)
        starterDict.update ({'shutter_speed' : shutter_speed})
        # videoFormat
        videoFormat = starterDict.get ('format', 'h264' )
        tempInput = input ('Set Video format for recording movies (currently ' + videoFormat + ') to :')
        if tempInput != '':
            videoFormat = tempInput
        starterDict.update ({'format' : videoFormat})
        # quality
        quality = starterDict.get ('quality', 20)
        tempInput = input ('Set Video quality for h264 movies, best=1, worst =40,0 for auto (currently ' + str (quality) + ') to :')
        if tempInput != '':
            quality = int (tempInput)
        starterDict.update ({'quality' : quality})
        # preview window
        previewWin = starterDict.get ('previewWin', (0,0,640,480))
        tempInput = input ('Set video preview window, left, top, right, bottom, (currently ' + str(previewWin) + ') to :')
        if tempInput != '':
            previewWin = tuple (int(x) for x in tempInput.split (','))
        starterDict.update ({'previewWin' : previewWin})
        # white balance
        whiteBalance = starterDict.get ('whiteBalance', False)
        tempInput = input ('Set white balancing for video, 1 for True, or 0 for False (currently ' + str (whiteBalance) + ') to :')
        if tempInput !='':
            tempInput = bool (int (tempInput))
        starterDict.update ({'whiteBalance' : whiteBalance})
        # return already modified dictionary, needed when making a new dictionary
        return starterDict


    def setup (self):
        try:
            self.piCam = PiCamera()
        except Exception as anError:
            print ("Error initializing camera.." + str (anError))
            raise anError
        # set fields in Picamera
        self.piCam.resolution = self.settingsDict.get ('resolution', (640, 480))
        self.piCam.framerate = self.settingsDict.get ('framerate', 30)
        self.piCam.iso = self.settingsDict.get ('iso', 0)
        self.piCam.shutter_speed = self.settingsDict.get ('shutter_speed', 30000)
        # set fields that are in AHF_Camera class
        self.AHFvideoFormat = self.settingsDict.get ('format', 'h264')
        self.AHFvideoQuality = self.settingsDict.get ('quality', 20)
        self.AHFframerate= self.settingsDict.get ('framerate', 30)
        self.AHFpreview = self.settingsDict.get('previewWin', (0,0,640,480))
        whiteBalance = self.settingsDict.get ('whiteBalance', False)
        self.AHFgainMode = (whiteBalance == True) # set bit 0 of gain for auto white balancing
        self.AHFgainMode += 2 * (self.piCam.iso == 0) # set bit 1 for auto gain
        # turn off LED on camera
        self.piCam.led = False
        # set gain based on 2 sec preview
        self.set_gain ()
        return

    def resolution(self):
        return self.piCam.resolution

    def hardwareTest (self):
        """
        Tests functionality, gives user a chance to change settings
        """
        print('Now displaying current output')
        self.piCam.start_preview(fullscreen = False, window=self.AHFpreview)
        result = input('Do you wish to edit Camera settings?')
        while result [0].lower() != 'y' and result[0].lower() !='n':
            result = input('Do you wish to edit Camera settings? (Y/N)')
        if result [0] == 'y' or result [0] == 'Y':
            self.setdown ()
            self.settingsDict = self.config_user_get (self.settingsDict)
            self.setup ()
        self.piCam.stop_preview()
        pass

    def setdown (self):
        """
        Writes session end and closes log file
        """
        self.piCam.close()
        pass

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
            DescStr += "from ISO " + str (self.piCam.iso)
        if (self.AHFgainMode & 1):
            DescStr += ' with white balancing'
        else:
            DescStr += " with No white balancing"
        print (DescStr)
        if (self.AHFgainMode & 1):
            self.piCam.awb_mode='auto'
        else:
            self.piCam.awb_mode='off'
            self.piCam.awb_gains = (1,1)
        #if (self.AHFgainMode & 2):
        self.exposure_mode = 'auto'
        #else:
        #    self.exposure_mode = 'off'
        self.piCam.start_preview(fullscreen = False, window=self.AHFpreview)
        sleep(2.0) # let gains settle, then fix values
        if (self.AHFgainMode & 1):
            savedGain = self.piCam.awb_gains
            self.piCam.awb_gains = savedGain
            self.piCam.awb_mode = "off"
        #if (self.AHFgainMode & 2):
        self.exposure_mode = 'off'
        self.piCam.stop_preview ()
        print ("Red Gain for white balance =" + str (float(self.piCam.awb_gains [0])))
        print ("Blue Gain for white balance =" + str (float(self.piCam.awb_gains [1])))
        print ("Analog Gain = " + str(float (self.piCam.analog_gain)))
        print ("Digital Gain = " + str (float(self.piCam.digital_gain)))
        return

    def capture(self, path, type, video_port =False):
        self.piCam.capture(path, type, use_video_port=video_port)

    def start_recording(self, video_name_path):
        """
        Starts a video recording using the saved settings for format, quality, gain, etc.

        A preview of the recording is always shown

        :param video_name_path: a full path to the file where the video will be stored. Always save to a file, not a PIL, for, example
        """
        if self.AHFvideoFormat == 'rgb':
            self.piCam.start_recording(output=video_name_path, format=self.AHFvideoFormat)
        else:
            self.piCam.start_recording(video_name_path, format = self.AHFvideoFormat, quality = self.AHFvideoQuality)
        self.piCam.start_preview(fullscreen = False, window= self.AHFpreview)
        return

    def add_overlay(self, bytes, layer, alpha):
        return self.piCam.add_overlay(bytes, layer=layer, alpha = alpha, fullscreen=False, window= self.AHFpreview)

    def remove_overlay(self, overlay):
        self.piCam.remove_overlay(overlay)


    def start_preview(self):
        self.piCam.start_preview(fullscreen = False, window= self.AHFpreview)

    def stop_preview(self):
        self.piCam.stop_preview()

    def stop_recording(self):
        """
        Stops a video recording previously started with start_recording.
        """
        if self.piCam.recording:
            self.piCam.stop_recording()
            self.piCam.stop_preview()
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
            self.piCam.start_recording(output=video_name_path, format=self.AHFvideoFormat)
        else:
            self.piCam.start_recording(output=video_name_path, format=self.AHFvideoFormat)
        self.piCam.start_preview(fullscreen = False, window= self.AHFpreview)
        self.piCam.wait_recording(timeout=recTime)
        self.stop_recording ()
        return


if __name__ == '__main__':
    import time
    import PTSimpleGPIO
    from PTSimpleGPIO import PTSimpleGPIO, Pulse, Train, Infinite_train

    t1 = Train (PTSimpleGPIO.MODE_FREQ, 14.4, 0.5, 30, 17, PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)

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
