from AHF_Stimulator_Rewards import AHF_Stimulator_Rewards
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse, Mice
from AHF_Camera import AHF_Camera
from picamera import PiCamera
from pynput import keyboard
import numpy as np
from PTPWM import PTPWM
from array import array
from queue import Queue as queue
from threading import Thread
from multiprocessing import Process, Queue
from time import sleep
from itertools import combinations,product
import imreg_dft as ird
import matplotlib.pyplot as plt
import warnings
#RPi module
import RPi.GPIO as GPIO

class AHF_Stimulator_Laser (AHF_Stimulator_Rewards):
    def __init__ (self, configDict, rewarder, lickDetector, textfp, camera):
        super().__init__(configDict, rewarder, lickDetector, textfp, camera)
        self.setup()

    def setup (self):
        super().setup()
        #Shift register controlled by 4 GPIOs
        self.DS = int(self.configDict.get('DS', 4))
        self.Q7S = int(self.configDict.get('Q7S', 6))
        self.SHCP = int(self.configDict.get('SHCP', 5))
        self.STCP = int(self.configDict.get('STCP', 17))
        self.PWM_mode = int(self.configDict.get('PWM_mode', 0))
        self.PWM_channel = int(self.configDict.get('PWM_channel', 1))
        self.array = array('i',(0 for i in range(1000)))
        self.PWM = PTPWM(1,1000,1000,0,(int(1E6/1000)),1000,2) #PWM object
        self.PWM.add_channel(self.PWM_channel,0,self.PWM_mode,0,0,self.array)
        self.PWM.set_PWM_enable(1,self.PWM_channel,0)
        self.duty_cycle = int(self.configDict.get('duty_cycle', 0))
        self.laser_on_time = int(self.configDict.get('laser_on_time', 0))
        self.delay = self.configDict.get('motor_delay', 0.03)
        
        #Overlay settings
        self.ratio = self.camera.resolution[0]/self.camera.resized[0]
        self.overlay_resolution = self.camera.resolution
        self.cross_pos = (np.array(self.camera.resolution)/2).astype(int)
        self.cross_step = int(self.camera.resolution[0]/50)
        self.cross_q = queue(maxsize=0) #Queues the cross-pin changes
        
        #Stepper settings
        GPIO.setup(self.SHCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.DS, GPIO.OUT, initial = GPIO.LOW)
        GPIO.setup(self.STCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.Q7S, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        
        self.mot_q = Queue(maxsize=0) #Queues steper motor commands
        self.phase_queue = Queue(maxsize=0) #Returns the new phase of the motors
        self.phase_queue.put([0,0])
        self.pos = np.array([0,0])
        self.laser_points = []
        self.image_points = []
        
#===================== Utility functions for the stepper motors and laser =================

    def unlock(self):
        GPIO.output(self.DS,0)
        for i in range(8):
            GPIO.output(self.SHCP,0)
            GPIO.output(self.SHCP,1)
        GPIO.output(self.STCP,0)
        GPIO.output(self.STCP,1)
        print('\n\nMotors unlocked.\n\n')

    def feed_byte(self,byte):
        for j in reversed(byte):
            GPIO.output(self.DS,j)
            GPIO.output(self.SHCP,0)
            GPIO.output(self.SHCP,1)
        GPIO.output(self.STCP,0)
        GPIO.output(self.STCP,1)

    def get_state(self):
        # Create empty array to store the state
        state = np.empty(8,dtype=int)
        # Read out serial output and store info
        for j in reversed(range(8)):
            out = GPIO.input(self.Q7S)
            np.put(state,j,out)
            GPIO.output(self.DS,out) #Feed output into input
            GPIO.output(self.SHCP,0)
            GPIO.output(self.SHCP,1)
        return state.tolist()

    def get_dir(self,steps):
        if steps > 0:
            return 1
        elif steps < 0:
            return -1
        else:
            return 0

    def rounding(self,width,height):
        #The overlay-width and height must be a multiple of 32/16
        if width%32 and height%16:
            return width + 32 - width%32,height + 16 - height%16
        elif width%32 and not height%16:
            return width + 32 - width%32,height
        elif height%16 and not width%32:
            return width,height + 16 - height%16
        else:
            return width,height

    def get_arrow_dir(self,key):
        if hasattr(key,'char'):
            self.kb.press(keyboard.Key.backspace)
            self.kb.release(keyboard.Key.backspace)
            return 0,0,0,0
        elif key == keyboard.Key.right:
            return 1,0,0,0
        elif key == keyboard.Key.left:
            return -1,0,0,0
        elif key == keyboard.Key.down:
            return 0,1,0,0
        elif key == keyboard.Key.up:
            return 0,-1,0,0
        elif key == keyboard.Key.delete:
            return 0,0,0,-self.cross_step
        elif key == keyboard.Key.page_down:
            return 0,0,0,self.cross_step
        elif key == keyboard.Key.home:
            return 0,0,-self.cross_step,0
        elif key == keyboard.Key.end:
            return 0,0,self.cross_step,0
        else:
            return 0,0,0,0

    def on_press(self,key):
        di = self.get_arrow_dir(key)
        if any(np.asarray(di[:2])!=0):
            self.mot_q.put(di[:2])
            self.pos += np.asarray(di[:2]) #Update the motor position
        if any(np.asarray(di[2:])!=0):
            self.cross_q.put(di[2:])
        if key == keyboard.Key.space:
            self.kb.press(keyboard.Key.backspace)
            self.kb.release(keyboard.Key.backspace)
            self.image_points.append(np.copy(self.cross_pos/self.ratio))
            self.laser_points.append(np.copy(np.flip(self.pos,axis=0)))
            print('\n\nPosition saved!\n\n')
        if key == keyboard.Key.esc:
            if len(self.image_points)>=3:
                self.image_points = np.asarray(self.image_points)
                self.laser_points = np.asarray(self.laser_points)
                try:
                    self.cross_q.task_done()
                    self.phase_q.task_done()
                    self.cross_q.put(None)#To terminate the thread
                except:
                    pass
                # Stop listener
                return False
            else:
                print('\n\nNeed at least 3 points!\n\n')
                pass

    def make_cross(self):
        cross = np.zeros((self.overlay_resolution[0],self.overlay_resolution[0],3),dtype=np.uint8)
        cross[self.cross_pos[0],:,:] = 0xff
        cross[:,self.cross_pos[1],:] = 0xff
        self.l3 = self.camera.add_overlay(cross.tobytes(),
                            layer=3,
                            alpha=100,
                            fullscreen=False,
                            window = self.camera.AHFpreview)

    def update_cross(self,q):
        while True:
            if not q.empty():    
                prod = q.get()
                if prod is None:
                    return False
                next_pos = self.cross_pos + np.array(prod)
                #Make sure the cross remains within the boundaries given by the overlay
                if not any((any(next_pos<0),any(next_pos>=np.array(self.camera.AHFpreview[2:])))):
                    self.cross_pos = next_pos
                    self.camera.remove_overlay(self.l3)
                    self.make_cross()
                else:
                    pass

    def update_mot(self,mot_q,phase_queue,delay,topleft):
        while True:
            if not mot_q.empty():
                x,y = mot_q.get()
                self.move(x,y,phase_queue,delay,topleft)
                self.pos += np.array([x,y])

    def move(self,x,y,phase_queue,delay,topleft):
        phase_x,phase_y = phase_queue.get()
        
        states = [[1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
                  [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1]]

        if topleft==True:
            x-=30
            y-=30

        if abs(x)>=abs(y):
            x_steps = np.arange(start=0,stop=abs(x),dtype=int)
            #y_steps = np.arange(start=0,stop=abs(y),dtype=int)
            y_steps = np.linspace(start=0,stop=abs(x-1),num=abs(y),endpoint=False,dtype=int)
        else:
            y_steps = np.arange(start=0,stop=abs(y),dtype=int)
            #x_steps = np.arange(start=0,stop=abs(x),dtype=int)
            x_steps = np.linspace(start=0,stop=abs(y-1),num=abs(x),endpoint=False,dtype=int)

        for i in (i for i in x_steps if x_steps.size>=y_steps.size):
            next_phase_x = (phase_x + self.get_dir(x)) % len(states)
            if i in y_steps:
                next_phase_y = (phase_y + self.get_dir(y)) % len(states)
                byte = states[next_phase_x]+states[next_phase_y]
                phase_y = next_phase_y
            else:
                state_y = self.get_state()[-4:]
                byte = states[next_phase_x]+state_y
            #Send and execute new byte
            self.feed_byte(byte)
            #Update phase
            phase_x = next_phase_x
            sleep(delay)

        for i in (i for i in y_steps if y_steps.size>x_steps.size):
            next_phase_y = (phase_y + self.get_dir(y)) % len(states)
            if i in x_steps:
                next_phase_x = (phase_x + self.get_dir(x)) % len(states)
                byte = states[next_phase_x]+states[next_phase_y]
                phase_x = next_phase_x
            else:
                state_x = self.get_state()[:4]
                byte = state_x+states[next_phase_y]
            #Send and execute new byte
            self.feed_byte(byte)
            phase_y = next_phase_y
            sleep(delay)
            
        if topleft == True:
            x = 30
            y = 30
            for i in np.arange(start=0,stop=30,dtype=int):
                next_phase_x = (phase_x + self.get_dir(x)) % len(states)
                next_phase_y = (phase_y + self.get_dir(y)) % len(states)
                byte = states[next_phase_x]+states[next_phase_y]
                #Send and execute new byte
                self.feed_byte(byte)
                #Update phase
                phase_x = next_phase_x
                phase_y = next_phase_y
                sleep(delay)
            self.unlock()
               
        #Save the phase. This is the only output needed.
        phase_queue.put([phase_x,phase_y])

    def move_to(self, new_x, new_y,topleft=True,join=False):
        steps_x = int(round(new_x)) - self.pos[0]
        steps_y = int(round(new_y)) - self.pos[1]
        mp = Process(target=self.move, args=(steps_x,steps_y,self.phase_queue,self.delay,topleft,))
        self.pos += np.array([steps_x,steps_y])
        mp.daemon = True
        mp.start()
        if join:
            mp.join()

    def pulse(self,duration,duty_cycle=0):
        if duration<=1000:
            for i in range(len(self.array)):
                self.array[i] = 0
            for i in range(1,duration):
                self.array[i]=duty_cycle
            self.PWM.start_train()
        else:
            print('Duration must be below 1000 ms.')


#==== Functions to perform the matching, target selection and image registration ====

    def matcher(self):
        #Matcher gets called through the crtl-c menu.
        def solver(image_points,laser_points):
            #Takes 3 points defined in laser- and image-coordinates and returns the coefficient matrix
            a=np.column_stack((image_points,np.array([1,1,1])))
            b1=laser_points[:,0]
            b2=laser_points[:,1]
            return np.vstack((np.linalg.solve(a, b1),np.linalg.solve(a, b2)))

        print('\nINSTRUCTION\n')
        print('Move:\tLaser\t\tcross hairs')
        print('---------------------------------------')
        print('Keys:\tarrow keys\tdelete home end page-down\n')
        print('1.: Move the laser and the cross hairs to at least 3 different points and hit the space key to save a point.')
        print('2.: To exit, hit the esc key.\n\n')

        try:
            #Turn on the laser
            self.pulse(1000,5) #If duration = 1000, laser stays on.
            #Start camera preview
            self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))

            self.make_cross()
            #Start the thread which updates the cross
            t = Thread(target = self.update_cross,args=(self.cross_q,))
            t.setDaemon(True)
            t.start()

            #Start the process which updates the motor
            mp = Process(target=self.update_mot, args=(self.mot_q,self.phase_queue,self.delay,False,))
            mp.daemon = True
            mp.start()
            
            #Make object for the keyboard Controller
            self.kb = keyboard.Controller()

            #Start the thread which listens to the keyboard
            with keyboard.Listener(on_press=self.on_press) as k_listener:
                k_listener.join()
        finally:
            self.move_to(0,0,topleft=True,join=False)
            k_listener.stop()
            mp.terminate()
            #Turn off the laser
            self.pulse(0)
            self.camera.stop_preview()
            self.camera.remove_overlay(self.l3)
            

        #======================Calculation================================
        #Average the coefficient matrix obatained by solving all combinations of triplets.
        
        self.coeff = []
        for i in combinations(enumerate(zip(self.image_points,self.laser_points)),3):
            ip = np.vstack((i[0][1][0],i[1][1][0],i[2][1][0]))
            lp = np.array([i[0][1][1],i[1][1][1],i[2][1][1]])
            self.coeff.append(solver(ip, lp))
        self.coeff = np.mean(np.asarray(self.coeff),axis=0)
        print(self.coeff)

    def get_ref_im(self):
        #Save a reference image whithin the mouse object
        self.mouse.target_im = np.empty((np.prod(np.asarray(self.camera.resolution)) * 3),dtype=np.uint8)

        #self.camera.wait_recording(1)
        self.camera.capture(self.mouse.target_im,'rgb')
        #self.camera.wait_recording(1)
        self.mouse.target_im = self.mouse.target_im.reshape((self.camera.resolution[0],self.camera.resolution[1],3))

        self.mouse.ref_im = np.empty((self.camera.resized[0], self.camera.resized[1], 3),dtype=np.uint8)
        warnings.filterwarnings("ignore",".*you may find the equivalent alpha format faster*")
        self.camera.capture(self.mouse.ref_im,'rgb',resize=self.camera.resized)

        self.mouse.tot_entries += 1

    def select_targets(self,mice):
        
        #========================GUI function for the selecting targets=====================
        def manual_annot(img):
            warnings.filterwarnings("ignore",".*GUI is implemented.*")
            fig = plt.figure(figsize=(10,10))
            imgplot = plt.imshow(img)
            plt.title('Choose targets')
            plt.show(block=False)
            points = np.around(np.asarray(plt.ginput(n=200,show_clicks=True,timeout=0)))
            plt.close()
            xses = map(int,[t[1] for t in points])
            yses = map(int,[t[0] for t in points])
            return list(xses),list(yses)

        if not hasattr(self,'coeff'):
            print('Need to perform the matching first before selecting targets')
            return None
        else:
            for mouse in mice.mouseArray:
                print('Mouse: ',mouse.tag)
                mouse.targets = {}
                targets_coords = manual_annot(mouse.target_im)
                targets_coords = list(zip(np.array(targets_coords[0]),np.array(targets_coords[1])))

                for i,j in enumerate(targets_coords):
                    target = 'target_'+str(i)
                    mouse.targets[target]=np.array(np.asarray(j)/self.ratio).astype(int) #Scale coordinate to desired size

                print('TARGET\tx\ty')
                for key,value in mouse.targets.items():
                    print('{0}\t{1}\t{2}'.format(key[-1],value[0],value[1]))

    def next_trial(self,video_name_path):
        
        #============Utility function to get the rotation matrix=================
        
        def trans_mat(angle,x,y,scale):
            angle = -1*np.radians(angle)
            scale = 1/scale
            x = -1*x
            y = -1*y
            rot_ext = np.array([[np.cos(angle),-np.sin(angle),y*np.cos(angle)-x*np.sin(angle)],
                                [np.sin(angle),np.cos(angle),y*np.sin(angle)+x*np.cos(angle)]])
            scale_mat = np.array([[scale,1,1],[1,scale,1]])
            return rot_ext*scale_mat

        trial = np.empty((self.camera.resized[0], self.camera.resized[1], 3),dtype=np.uint8)
        warnings.filterwarnings("ignore",".*you may find the equivalent alpha format faster*")
        #self.camera.wait_recording(1)
        self.camera.capture(trial,'rgb',resize=self.camera.resized)
        #self.camera.wait_recording(1)
        
        try:
            warnings.filterwarnings("ignore",".*the returned array has changed*")
            tf = ird.similarity(self.mouse.ref_im[:,:,0],trial[:,:,0],numiter=3)
            print('scale\tangle\tty\ttx')
            print('{0:.3}\t{1:.3}\t{2:.3}\t{3:.3}'.format(tf['scale'],tf['angle'],tf['tvec'][0],tf['tvec'][1]))

            #start recording
            #self.camera.start_recording(video_name_path)

            #Transform the reference targets
            R = trans_mat(tf['angle'],tf['tvec'][1],tf['tvec'][0],tf['scale'])
            print('TARGET\ttx\tty')
            for key,value in self.mouse.targets.items():
                value = np.asarray(value) - np.array([int(self.camera.resized[0]/2),int(self.camera.resized[0]/2)]) #translate targets to center of image
                trans_coord = np.dot(R,np.append(value,1))+np.array([int(self.camera.resized[0]/2),int(self.camera.resized[0]/2)])
                targ_pos = np.dot(self.coeff,np.append(trans_coord,1))
                print('{0}\t{1:.01f}\t{2:.01f}'.format(key,trans_coord[0],trans_coord[1]))
                self.move_to(targ_pos[1],targ_pos[0],topleft=True,join=True)
                self.pulse(self.laser_on_time,self.duty_cycle)
                sleep(1)
        finally:
            #stop recording
            #self.camera.stop_recording()
            self.move_to(0,0,topleft=True,join=False)

#=================Main functions called from outside===========================

    def run(self,video_name_path):
        self.rewardTimes = []
        self.stimTimes = []
        #Check if mouse is here for the first time. If yes -> get_ref_im
        if self.mouse.tot_entries == 1:
            print('Take ref im')
            self.get_ref_im()
            return
        elif not hasattr(self.mouse,'targets'):
            print('Select targets')
            #Check whether brain targets have been choosen or not
            return
        print('Next trial')
        self.next_trial(video_name_path)

    def tester(self,mice):
        inputStr = input ('m= matching, t= select targets: ')
        if inputStr == 'm':
            self.matcher()
        elif inputStr == 't':
            self.select_targets(mice)


if __name__ == '__main__':
    #Local files, part of AutoHeadFix
    from AHF_Settings import AHF_Settings
    from AHF_CageSet import AHF_CageSet
    from AHF_Camera import AHF_Camera
    from AHF_Notifier import AHF_Notifier
    from RFIDTagReader import TagReader
    from AHF_Stimulator import AHF_Stimulator
    from AHF_UDPTrig import AHF_UDPTrig
    from AHF_HardwareTester import hardwareTester
    from AHF_Mouse import Mouse, Mice
    from AHF_HeadFixer import AHF_HeadFixer
    from AHF_LickDetector import AHF_LickDetector, Simple_Logger
    
    #Standard Python modules
    from os import path, makedirs, chown
    from pwd import getpwnam
    from grp import getgrnam
    from time import time, localtime, timezone, sleep
    from datetime import datetime
    from random import random
    from sys import argv,exit

    def makeDayFolderPath (expSettings, cageSettings):
        """
        Makes data folders for a day's data,including movies, log file, and quick stats file

        Format: dayFolder = cageSettings.dataPath + cageSettings.cageID + YYYMMMDD
        within which will be /Videos and /TextFiles
        :param expSettings: experiment-specific settings, everything you need to know is stored in this object
        :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO

        """
        dateTimeStruct = localtime()
        expSettings.dateStr= str (dateTimeStruct.tm_year) + (str (dateTimeStruct.tm_mon)).zfill(2) + (str (dateTimeStruct.tm_mday)).zfill(2)
        expSettings.dayFolderPath = cageSettings.dataPath + expSettings.dateStr + '/' + cageSettings.cageID + '/'
        try:
            if not path.exists(expSettings.dayFolderPath):
                makedirs(expSettings.dayFolderPath, mode=0o777, exist_ok=True)
                makedirs(expSettings.dayFolderPath + 'TextFiles/', mode=0o777, exist_ok=True)
                makedirs(expSettings.dayFolderPath + 'Videos/', mode=0o777, exist_ok=True)
                uid = getpwnam ('pi').pw_uid
                gid = getgrnam ('pi').gr_gid
                chown (expSettings.dayFolderPath, uid, gid)
                chown (expSettings.dayFolderPath + 'TextFiles/', uid, gid)
                chown (expSettings.dayFolderPath + 'Videos/', uid, gid)
        except Exception as e:
                print ("Error maing directories\n", str(e))
            

    def makeLogFile (expSettings, cageSettings):
        """
        open a new text log file for today, or open an exisiting text file with 'a' for append
        """
        try:
            logFilePath = expSettings.dayFolderPath + 'TextFiles/headFix_' + cageSettings.cageID + '_' + expSettings.dateStr + '.txt'
            expSettings.logFP = open(logFilePath, 'a')
            uid = getpwnam ('pi').pw_uid
            gid = getgrnam ('pi').gr_gid
            chown (logFilePath, uid, gid)
            writeToLogFile (expSettings.logFP, None, 'SeshStart')
        except Exception as e:
                print ("Error maing log file\n", str(e))
                
    def writeToLogFile(logFP, mouseObj, event):
        """
        Writes the time and type of each event to a text log file, and also to the shell

        Format of the output string: tag     time_epoch or datetime       event
        The computer-parsable time_epoch is printed to the log file and user-friendly datetime is printed to the shell
        :param logFP: file pointer to the log file
        :param mouseObj: the mouse for which the event pertains, 
        :param event: the type of event to be printed, entry, exit, reward, etc.
        returns: nothing
        """
        try:
            if event == 'SeshStart' or event == 'SeshEnd' or mouseObj is None:
                outPutStr = ''.zfill(13)
            else:
                outPutStr = '{:013}'.format(mouseObj.tag)
            logOutPutStr = outPutStr + '\t' + '{:.2f}'.format (time ())  + '\t' + event +  '\t' + datetime.fromtimestamp (int (time())).isoformat (' ')
            printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
            print (printOutPutStr)
            logFP.write(logOutPutStr + '\n')
            logFP.flush()
        except Exception as e:
            print ("Error writing to log file\n", str (e))

    def makeQuickStatsFile (expSettings, cageSettings, mice):
        """
        makes a new quickStats file for today, or opens an existing file to append.
        
        QuickStats file contains daily totals of rewards and headFixes for each mouse
        :param expSettings: experiment-specific settings, everything you need to know is stored in this object
        :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
        :param mice: the array of mice objects for this cage
    """
        try:
            textFilePath = expSettings.dayFolderPath + 'TextFiles/quickStats_' + cageSettings.cageID + '_' + expSettings.dateStr + '.txt'
            if path.exists(textFilePath):
                expSettings.statsFP = open(textFilePath, 'r+')
                mice.addMiceFromFile(expSettings.statsFP)
                mice.show()
            else:
                expSettings.statsFP = open(textFilePath, 'w')
                expSettings.statsFP.write('Mouse_ID\tentries\tent_rew\thfixes\thf_rew\n')
                expSettings.statsFP.close()
                expSettings.statsFP = open(textFilePath, 'r+')
                uid = getpwnam ('pi').pw_uid
                gid = getgrnam ('pi').gr_gid
                chown (textFilePath, uid, gid)
        except Exception as e:
            print ("Error making quickStats file\n", str (e))

    def updateStats (statsFP, mice, mouse):
        """ Updates the quick stats text file after every exit, mostly for the benefit of folks logged in remotely
        :param statsFP: file pointer to the stats file
        :param mice: the array of mouse objects
        :param mouse: the mouse which just left the chamber 
        returns:nothing
        """
        try:
            pos = mouse.arrayPos
            statsFP.seek (39 + 38 * pos) # calculate this mouse pos, skipping the 39 char header
            # we are in the right place in the file and new and existing values are zero-padded to the same length, so overwriting should work
            outPutStr = '{:013}'.format(mouse.tag) + "\t" +  '{:05}'.format(mouse.entries)
            outPutStr += "\t" +  '{:05}'.format(mouse.entranceRewards) + "\t" + '{:05}'.format(mouse.headFixes)
            outPutStr +=  "\t" + '{:05}'.format(mouse.headFixRewards) + "\n"
            statsFP.write (outPutStr)
            statsFP.flush()
            statsFP.seek (39 + 38 * mice.nMice()) # leave file position at end of file so when we quit, nothing is truncated
        except Exception as e:
            print ("Error writing updating stat file\n", str (e))


    def entryBBCallback (channel):
        global gTubePanicTime # the global indicates that it is the same variable declared above and also used by main
        global gTubeMaxTime
        global gMouseAtEntry
        if GPIO.input (channel) == GPIO.LOW: # mouse just entered
            if gMouseAtEntry == False:
                print ('mouse at entrance')
            gMouseAtEntry =True
            gTubePanicTime = time () + gTubeMaxTime
            
        elif GPIO.input (channel) == GPIO.HIGH:  # mouse just left
            if gMouseAtEntry == True:
                print ('Mouse left entrance')
            gMouseAtEntry =False
            gTubePanicTime = time () + 25920000 # a month from now.

    def runTrial (thisMouse, expSettings, cageSettings, camera, rewarder, headFixer, stimulator, UDPTrigger=None):
        """
        Runs a single AutoHeadFix trial, from the mouse making initial contact with the plate

        Controls turning on and off the blue brain illumination LED, starting and stopping the movie, and running the stimulus
        which includes giving rewards
            :param thisMouse: the mouse object representing nouse that is being head-fixed
            :param expSettings: experiment-specific settings, everything you need to know is stored in this object
            :param cageSettings: settings that are expected to stay the same for each setup, including hardware pin-outs for GPIO
            :param camera: The AHF_Camera object used to record video
            :param rewarder :object of AHF_Rewarder class that runs solenoid to give water rewards
            :param stimulator: object of a subclass of  AHF_Stimulator, which runs experiment, incuding giving rewards
            :param UDPTrigger: used if sending UDP signals to other Pi for behavioural observation
        """
        try:
            if expSettings.doHeadFix == True:
                headFixer.fixMouse()
                sleep(0.4) # wait a bit for things to settle, then re-check contacts
                if GPIO.input(cageSettings.contactPin) == expSettings.noContactState:
                    # release mouse if no contact... :(
                    headFixer.releaseMouse()
                    writeToLogFile(expSettings.logFP, thisMouse, 'check-')
                    return False
            #  non-head fix trial or check was successful
            if expSettings.doHeadFix == True:
                thisMouse.headFixes += 1
                writeToLogFile (expSettings.logFP, thisMouse, 'check+')
            else:
                writeToLogFile (expSettings.logFP, thisMouse,'check No Fix Trial')
            # Configure the stimulator and the path for the video
            #=========Saves mouse data to stimulator==============================
            stimStr = stimulator.configStim (thisMouse)
            headFixTime = time()
            
            #TODO IMPROVE
            if camera.AHFvideoFormat == 'rgb':
                extension = 'raw'
            else:
                extension = 'h264'

            video_name = str (thisMouse.tag) + "_" + stimStr + "_" + '%d' % headFixTime + '.' + extension
            video_name_path = expSettings.dayFolderPath + 'Videos/' + "M" + video_name
            writeToLogFile (expSettings.logFP, thisMouse, "video:" + video_name)
            # send socket message to start behavioural camera
            if expSettings.hasUDP == True:
                #MESSAGE = str (thisMouse.tag) + "_" + stimStr + "_" + '%d' % headFixTime
                MESSAGE = str (thisMouse.tag) + "_" +  "_" + '%d' % headFixTime
                UDPTrigger.doTrigger (MESSAGE)
                # start recording and Turn on the blue led
                camera.start_recording(video_name_path)
                sleep(expSettings.cameraStartDelay) # wait a bit so camera has time to start before light turns on, for synchrony accross cameras
                GPIO.output(cageSettings.ledPin, GPIO.HIGH)
                writeToLogFile (expSettings.logFP, thisMouse, "BrainLEDON")
            else: # turn on the blue light and start the movie
                GPIO.output(cageSettings.ledPin, GPIO.HIGH)
                #camera.start_recording(video_name_path)
            stimulator.run (video_name_path) # run whatever stimulus is configured
            if expSettings.hasUDP == True:
                GPIO.output(cageSettings.ledPin, GPIO.LOW) # turn off the blue LED
                writeToLogFile (expSettings.logFP, thisMouse, "BrainLEDOFF")
                sleep(expSettings.cameraStartDelay) #wait again after turning off LED before stopping camera, for synchronization
                UDPTrigger.doTrigger ("Stop") # stop
                camera.stop_recording()
            else:
                #camera.stop_recording()
                GPIO.output(cageSettings.ledPin, GPIO.LOW) # turn off the blue LED
            if path.isfile(video_name_path):
                uid = getpwnam ('pi').pw_uid
                gid = getgrnam ('pi').gr_gid
                chown (video_name_path, uid, gid) # we run AutoheadFix as root if using pi PWM, so we expicitly set ownership to pi
            # skeddadleTime gives mouse a chance to disconnect before head fixing again
            skeddadleEnd = time() + expSettings.skeddadleTime
            if expSettings.doHeadFix == True:
                headFixer.releaseMouse()
                sleep (0.5) # need to be mindful that servo motors generate RF, so wait 
            stimulator.logfile ()
            writeToLogFile (expSettings.logFP, thisMouse,'complete')
            if (GPIO.input (cageSettings.contactPin)== expSettings.contactState):
                while time () < skeddadleEnd:
                    GPIO.wait_for_edge (cageSettings.contactPin, expSettings.noContactEdge, timeout= kTIMEOUTmS)
                    if (GPIO.input (cageSettings.contactPin)== expSettings.noContactState):
                        break
            return True
        except Exception as anError:
            headFixer.releaseMouse()
            #camera.stop_recording()
            print ('Error in running trial:' + str (anError))
            raise anError

    # constants used for calculating when to start a new day
    # we put each day's movies and text files in a separate folder, and keep separate stats
    KSECSPERDAY = 86400
    KSECSPERHOUR = 3600
    KDAYSTARTHOUR =13 # when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM

    """
    constant for time outs when waiting on an event - instead of waiting for ever, and missing, e.g., keyboard event,
    or callling sleep and maybe missing the thing we were waiting for, we loop using wait_for_edge with a timeout
    """
    kTIMEOUTmS = 50

    gTubePanicTime =1
    gTubeMaxTime =1
    gMouseAtEntry =0

#Main program

    try:
        # load general settings for this cage, mostly hardware pinouts
        # things not expected to change often - there is only one AHFconfig.jsn file, in the enclosing folder
        cageSettings = AHF_CageSet()
        #print (cageSettings)
        # get settings that may vary by experiment, including rewarder, camera parameters, and stimulator
        # More than one of these files can exist, and the user needs to choose one or make one
        # we will add some other  variables to expSettings so we can pass them as a single argument to functions
        # logFP, statsFP, dateStr, dayFolderPath, doHeadFix, 
        # configFile can be specified if launched from command line, eg, sudo python3 myconfig or sudo python3 AHFexp_myconfig.jsn
        configFile = None
        if argv.__len__() > 1:
            configFile = argv [1]
        expSettings = AHF_Settings (configFile)
        # nextDay starts tomorrow at KDAYSTARTHOUR
        #nextDay = (int((time() - timezone)/KSECSPERDAY) + 1) * KSECSPERDAY + timezone + (KDAYSTARTHOUR * KSECSPERHOUR)
        nextDay = ((int((time() - timezone + localtime().tm_isdst * 3600)/KSECSPERDAY)) * KSECSPERDAY)  + timezone - (localtime().tm_isdst * 3600) + KSECSPERDAY + KDAYSTARTHOUR
        # Create folders where the files for today will be stored
        makeDayFolderPath(expSettings, cageSettings)
        # initialize mice with zero mice
        mice = Mice()
        # make daily Log files and quick stats file
        makeLogFile (expSettings, cageSettings)
        makeQuickStatsFile (expSettings, cageSettings, mice)
        # set up the GPIO pins for each for their respective functionalities.
        GPIO.setmode (GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup (cageSettings.ledPin, GPIO.OUT, initial = GPIO.LOW) # turns on brain illumination LED
        GPIO.setup (cageSettings.tirPin, GPIO.IN)  # Tag-in-range output from RFID tatg reader
        GPIO.setup (cageSettings.contactPin, GPIO.IN, pull_up_down=getattr (GPIO, "PUD_" + cageSettings.contactPUD))
        if cageSettings.contactPolarity == 'RISING':
            expSettings.contactEdge = GPIO.RISING 
            expSettings.noContactEdge = GPIO.FALLING
            expSettings.contactState = GPIO.HIGH
            expSettings.noContactState = GPIO.LOW
        else:
            expSettings.contactEdge = GPIO.FALLING
            expSettings.noContactEdge = GPIO.RISING 
            expSettings.contactState = GPIO.LOW
            expSettings.noContactState = GPIO.HIGH
        # make head fixer - does its own GPIO initialization from info in cageSettings
        headFixer=AHF_HeadFixer.get_class (cageSettings.headFixer) (cageSettings)
        # make a rewarder
        rewarder = AHF_Rewarder (30e-03, cageSettings.rewardPin)
        rewarder.addToDict('entrance', expSettings.entranceRewardTime)
        rewarder.addToDict ('task', expSettings.taskRewardTime)
        # make a notifier object
        if expSettings.hasTextMsg == True:
            notifier = AHF_Notifier (cageSettings.cageID, expSettings.phoneList)
        else:
            notifier = None
        # make RFID reader
        tagReader = TagReader(cageSettings.serialPort, False, None)
        # configure camera
        camera = AHF_Camera(expSettings.camParamsDict)
        # make UDP Trigger
        if expSettings.hasUDP == True:
            UDPTrigger = AHF_UDPTrig (expSettings.UDPList)
            print (UDPTrigger)
        else:
            UDPTrigger = None
        # make a lick detector
        simpleLogger = Simple_Logger (expSettings.logFP)
        lickDetector = AHF_LickDetector ((0,1),26,simpleLogger)
        sleep(1)
        lickDetector.start_logging ()
        # make stimulator
        stimulator = AHF_Stimulator.get_class (expSettings.stimulator)(expSettings.stimDict, rewarder, lickDetector, expSettings.logFP, camera)
        expSettings.stimDict = stimulator.configDict
        # Entry beam breaker
        if cageSettings.hasEntryBB==True:
            GPIO.setup (cageSettings.entryBBpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            GPIO.add_event_detect (cageSettings.entryBBpin, GPIO.BOTH, entryBBCallback)
            #GPIO.add_event_callback (cageSettings.entryBBpin, entryBBCallback)
            gTubePanicTime = time () + 25920000 # a month from now.
            gTubeMaxTime = expSettings.inChamberTimeLimit
    except Exception as anError:
        print ('Unexpected error starting AutoHeadFix:', str (anError))
        raise anError
        exit(0)
    try:    
        print ('Waiting for a mouse...')
        while True: #start main loop
            try:
                # wait for mouse entry, with occasional timeout to catch keyboard interrupt
                GPIO.wait_for_edge (cageSettings.tirPin, GPIO.RISING, timeout= kTIMEOUTmS) # wait for entry based on Tag-in-range pin
                if (GPIO.input (cageSettings.tirPin) == GPIO.HIGH):
                    try:
                        tag = tagReader.readTag ()
                    except (IOError, ValueError):
                        tagReader.clearBuffer()
                        continue
                    entryTime = time()
                    if cageSettings.hasEntryBB==True:
                        GPIO.remove_event_detect(cageSettings.entryBBpin)
                    thisMouse = mice.getMouseFromTag (tag)
                    if thisMouse is None:
                        # try to open mouse config file to initialize mouse data
                        thisMouse=Mouse(tag,1,0,0,0)
                        mice.addMouse (thisMouse, expSettings.statsFP)
                    writeToLogFile(expSettings.logFP, thisMouse, 'entry')
                    thisMouse.entries += 1
                    # if we have entrance reward, first wait for entrance reward or first head-fix, which countermands entry reward
                    if thisMouse.entranceRewards < expSettings.maxEntryRewards:
                        giveEntranceReward = True
                        expSettings.doHeadFix = expSettings.propHeadFix > random()                      
                        while GPIO.input (cageSettings.tirPin)== GPIO.HIGH and time() < (entryTime + expSettings.entryRewardDelay):
                            GPIO.wait_for_edge (cageSettings.contactPin, expSettings.contactEdge, timeout= kTIMEOUTmS)
                            if (GPIO.input (cageSettings.contactPin)== expSettings.contactState):
                                #======================runTrial================================================
                                runTrial (thisMouse, expSettings, cageSettings, camera, rewarder, headFixer,stimulator, UDPTrigger)
                                giveEntranceReward = False
                                break
                        if (GPIO.input (cageSettings.tirPin)== GPIO.HIGH) and giveEntranceReward == True:
                            thisMouse.reward (rewarder, 'entrance') # entrance reward was not countermanded by an early headfix
                            thisMouse.entranceRewards += 1
                            writeToLogFile(expSettings.logFP, thisMouse, 'entryReward')
                    # wait for contacts and run trials till mouse exits or time in chamber exceeded
                    expSettings.doHeadFix = expSettings.propHeadFix > random()
                    while GPIO.input (cageSettings.tirPin)== GPIO.HIGH and time () < entryTime + expSettings.inChamberTimeLimit:
                        if (GPIO.input (cageSettings.contactPin)== expSettings.noContactState):
                            GPIO.wait_for_edge (cageSettings.contactPin, expSettings.contactEdge, timeout= kTIMEOUTmS)
                        if (GPIO.input (cageSettings.contactPin)== expSettings.contactState):
                            runTrial (thisMouse, expSettings, cageSettings, camera, rewarder, headFixer, stimulator, UDPTrigger)
                            expSettings.doHeadFix = expSettings.propHeadFix > random() # set doHeadFix for next contact
                    # either mouse left the chamber or has been in chamber too long
                    if GPIO.input (cageSettings.tirPin)== GPIO.HIGH and time () > entryTime + expSettings.inChamberTimeLimit:
                        # explictly turn off pistons, though they should be off at end of trial
                        headFixer.releaseMouse()
                        if expSettings.hasTextMsg == True:
                            notifier.notify (thisMouse.tag, (time() - entryTime),  True)
                        # wait for mouse to leave chamber, with no timeout, unless it left while we did last 3 lines
                        if GPIO.input (cageSettings.tirPin)== GPIO.HIGH:
                            GPIO.wait_for_edge (cageSettings.tirPin, GPIO.FALLING)
                        if expSettings.hasTextMsg == True:
                            notifier.notify (thisMouse.tag, (time() - entryTime), False)
                    tagReader.clearBuffer ()
                    if cageSettings.hasEntryBB==True:
                        #GPIO.setup (cageSettings.entryBBpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
                        GPIO.add_event_detect (cageSettings.entryBBpin, GPIO.BOTH, entryBBCallback)
                    # after exit, update stats
                    writeToLogFile(expSettings.logFP, thisMouse, 'exit')
                    updateStats (expSettings.statsFP, mice, thisMouse)
                    # after each exit check for a new day
                    if time() > nextDay:
                        # stop lick logging so we dont write to file when it is closed 
                        lickDetector.stop_logging ()
                        mice.show()
                        writeToLogFile(expSettings.logFP, None, 'SeshEnd')
                        expSettings.logFP.close()
                        expSettings.statsFP.close()
                        makeDayFolderPath(expSettings, cageSettings)
                        makeLogFile (expSettings, cageSettings)
                        simpleLogger.logFP = expSettings.logFP
                        makeQuickStatsFile (expSettings, cageSettings, mice)
                        stimulator.nextDay (expSettings.logFP)
                        nextDay += KSECSPERDAY
                        mice.clear ()
                        # reinitialize lick detector because it can lock up if too many licks when not logging
                        lickDetector.__init__((0,1),26,simpleLogger)
                        lickDetector.start_logging()
                    print ('Waiting for a mouse...')
                else:
                    # check for entry beam break while idling between trials
                    if cageSettings.hasEntryBB==True and time() > gTubePanicTime:
                        print ('Some one has been in the entrance of this tube for too long')
                        # explictly turn off pistons, though they should be off 
                        headFixer.releaseMouse()
                        BBentryTime = gTubePanicTime - gTubeMaxTime
                        if expSettings.hasTextMsg == True:
                            notifier.notify (0, (time() - BBentryTime),  True) # we don't have an RFID for this mouse, so use 0
                        # wait for mouse to leave chamber
                        while time() > gTubePanicTime:
                            sleep (kTIMEOUTmS/1000)
                        print ('looks like some one managed to escape the entrance of this tube')
                        if expSettings.hasTextMsg == True:
                            notifier.notify (0, (time() - BBentryTime), False)
            except KeyboardInterrupt:
                GPIO.output(cageSettings.ledPin, GPIO.LOW)
                headFixer.releaseMouse()
                GPIO.output(cageSettings.rewardPin, GPIO.LOW)
                lickDetector.stop_logging ()
                if cageSettings.hasEntryBB==True:
                    sleep (1)
                    GPIO.remove_event_detect (cageSettings.entryBBpin)
                    print ('removed BB event detect')
                while True:
                    event = input ('Enter:\nr to return to head fix trials\nq to quit\nv to run valve control\nh for hardware tester\nc for camera configuration\ne for experiment configuration\n:')
                    if event == 'r' or event == "R":
                        lickDetector.start_logging ()
                        sleep (1)
                        if cageSettings.hasEntryBB == True:
                            sleep (1)
                            print ('Restarting entry bb')
                            GPIO.setup (cageSettings.entryBBpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
                            GPIO.add_event_detect (cageSettings.entryBBpin, GPIO.BOTH, entryBBCallback)
                        break
                    elif event == 'q' or event == 'Q':
                        exit(0)
                    elif event == 'v' or event== "V":
                        valveControl (cageSettings)
                    elif event == 'h' or event == 'H':
                        hardwareTester(cageSettings, tagReader, headFixer, stimulator, mice)
                        if cageSettings.contactPolarity == 'RISING':
                            expSettings.contactEdge = GPIO.RISING 
                            expSettings.noContactEdge = GPIO.FALLING
                            expSettings.contactState = GPIO.HIGH
                            expSettings.noContactState = GPIO.LOW
                        else:
                            expSettings.contactEdge = GPIO.FALLING
                            expSettings.noContactEdge = GPIO.RISING 
                            expSettings.contactState = GPIO.LOW
                            expSettings.noContactState = GPIO.HIGH
                    elif event == 'c' or event == 'C':
                        camParams = camera.adjust_config_from_user ()
                    elif event == 'e' or event == 'E':
                        modCode = expSettings.edit_from_user ()
                        if modCode & 2:
                           stimulator = AHF_Stimulator.get_class (expSettings.stimulator)(expSettings.stimDict, rewarder, lickDetector, expSettings.logFP)
                        if modCode & 1:
                            stimulator.change_config (expSettings.stimDict)
    except Exception as anError:
        print ('AutoHeadFix error:' + str (anError))
        raise anError
    finally:
        stimulator.quitting()
        GPIO.output(cageSettings.ledPin, False)
        headFixer.releaseMouse()
        GPIO.output(cageSettings.rewardPin, False)
        GPIO.cleanup()
        writeToLogFile(expSettings.logFP, None, 'SeshEnd')
        expSettings.logFP.close()
        expSettings.statsFP.close()
        print ('AutoHeadFix Stopped')
