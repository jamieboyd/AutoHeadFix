'''
This Stimulator is subclassed from Rewards. It captures a reference image for each
mouse and includes a user interface to select targets on reference images.
The Stimulator directs and pulses a laser to selected targets for optogenetic
stimulation/inhibition.
'''

#AHF-specific moudules
from PTSimpleGPIO import PTSimpleGPIO, Infinite_train, Train
from AHF_Rewarder import AHF_Rewarder
from AHF_Stimulus import AHF_Stimulus
from AHF_Mouse import Mouse, Mice

#Laser-stimulator modules
from pynput import keyboard
import numpy as np
import sys
from os import path
import matplotlib.pyplot as plt
from PTPWM import PTPWM
from array import array
from queue import Queue as queue
from threading import Thread
from multiprocessing import Process, Queue
from time import sleep, time
from random import randrange
from datetime import datetime
from itertools import combinations,product
import imreg_dft as ird
import warnings
from h5py import File

#RPi module
import RPi.GPIO as GPIO



class AHF_Stimulus_Laser (AHF_Stimulus):
    # def __init__ (self, cageSettings, expSettings, rewarder, lickDetector, camera):
    #     super().__init__(cageSettings, expSettings, rewarder, lickDetector, camera)
    #     self.setup()
    @staticmethod
    def about():
        return 'stimulates brain with laser, moved with stepper motor stage. MUST BE USED WITH PICAM'

    @staticmethod
    def config_user_get (starterDict = {}):
        defaultMode = 0
        defaultChannel = 2
        defaultDutyCycle = 0
        defaultLaserTime = 0
        defaultCoeff = None
        defaultDS = 4
        defaultQ7S = 6
        defaultSHCP = 5
        defaultSTCP = 17
        defaultDelay = 0.03
        defaultH5 = "mice_images.h5"
        #mode
        PWM_mode = starterDict.get ('PWM_mode', defaultMode)
        tempInput = input ('Set PWM mode (currently {0}): '.format(PWM_mode))
        if tempInput != '':
            PWM_mode = int (tempInput)
        starterDict.update ({'PWM_mode' : PWM_mode})
        #channel
        PWM_channel = starterDict.get ('PWM_channel', defaultChannel)
        tempInput = input ('Set PWM channel (currently {0}): '.format(PWM_channel))
        if tempInput != '':
            PWM_channel = int (tempInput)
        starterDict.update ({'PWM_channel' : PWM_channel})
        #duty cycle
        duty_cycle = starterDict.get ('duty_cycle', defaultDutyCycle)
        tempInput = input ('Set duty cycle (currently {0}): '.format(duty_cycle))
        if tempInput != '':
            duty_cycle = int (tempInput)
        starterDict.update ({'duty_cycle' : duty_cycle})
        #laser on time
        laser_on_time = starterDict.get ('laser_on_time', defaultLaserTime)
        tempInput = input ('Set how long the laser is on for (currently {0}): '.format(laser_on_time))
        if tempInput != '':
            laser_on_time = int (tempInput)
        starterDict.update ({'laser_on_time' : laser_on_time})
        #Crosshair Placement
        coeff_matrix = starterDict.get ('coeff_matrix', defaultCoeff)
        tempInput = input ('set X,Y coefficients for crosshair (currently {0}): '.format(coeff_matrix))
        if tempInput != '':
            coeff_matrix = tuple (int(x) for x in tempInput.split (','))
        starterDict.update ({'coeff_matrix' : coeff_matrix})
        print('Stepper Motor Settings:')
        print('--->Shift Register Settings:')
        DS = starterDict.get ('DS', defaultDS)
        tempInput = input ('Set DS (currently {0}): '.format(DS))
        if tempInput != '':
            DS = int (tempInput)
        starterDict.update ({'DS' : DS})
        Q7S = starterDict.get ('Q7S', defaultQ7S)
        tempInput = input ('Set Q7S (currently {0}): '.format(Q7S))
        if tempInput != '':
            Q7S = int (tempInput)
        starterDict.update ({'Q7S' : Q7S})
        SHCP = starterDict.get ('SHCP', defaultSHCP)
        tempInput = input ('Set SHCP (currently {0}): '.format(SHCP))
        if tempInput != '':
            SHCP = int (tempInput)
        starterDict.update ({'SHCP' : SHCP})
        STCP = starterDict.get ('STCP', defaultSTCP)
        tempInput = input ('Set STCP (currently {0}): '.format(STCP))
        if tempInput != '':
            STCP = int (tempInput)
        starterDict.update ({'STCP' : STCP})
        #End Shift Register Settings
        print('--->Other Settings:')
        motor_delay = starterDict.get ('motor_delay', defaultDelay)
        tempInput = input ('Set motor delay (currently {0}): '.format(motor_delay))
        if tempInput != '':
            motor_delay = float (tempInput)
        starterDict.update ({'motor_delay' : motor_delay})
        #h5
        hdf_path = starterDict.get ('hdf_path', defaultH5)
        tempInput = input ('Set HDF5 path (currently {0}): '.format(hdf_path))
        if tempInput != '':
            hdf_path = str (tempInput)
        starterDict.update ({'hdf_path' : hdf_path})
        return starterDict

    def setup (self):
        self.camera = self.task.Camera
        #PWM settings
        self.PWM_mode = int(self.settingsDict.get('PWM_mode', 0))
        self.PWM_channel = int(self.settingsDict.get('PWM_channel', 2))
        self.array = array('i',(0 for i in range(1000)))
        self.PWM = PTPWM(1,1000,1000,0,(int(1E6/1000)),1000,2) #PWM object
        self.PWM.add_channel(self.PWM_channel,0,self.PWM_mode,0,0,self.array)
        self.PWM.set_PWM_enable(1,self.PWM_channel,0)
        self.duty_cycle = int(self.settingsDict.get('duty_cycle', 0))
        self.laser_on_time = int(self.settingsDict.get('laser_on_time', 0))
        '''
        Info: The laser is controlled using the PTPWM class, which employs a hardsware
        pulse-width modulator to change the laser intensity. Read PWM Thread documentation
        for further information.
        '''

        #Cross-hair Overlay settings
        self.overlay_resolution = self.camera.resolution()
        self.cross_pos = (np.array(self.camera.resolution())/2).astype(int)
        self.cross_step = int(self.camera.resolution()[0]/50)
        self.cross_q = queue(maxsize=0) #Queues the cross-hair changes.
        self.coeff = np.asarray (self.settingsDict.get ('coeff_matrix', None))
        '''
        Info: A cross-hair is used as an overlay to the picamera preview. Commands
        to move the cross-hair are queued in a python queue, which is processed by
        a separate thread. An existing coefficient matrix is loaded from the settings.
        '''

        '''
        #Buzzer settings == Vibmotor
        #self.buzz_pulseProb = float (self.configDict.get ('buzz_pulseProb', 1))
        self.buzz_pin = int(self.configDict.get ('buzz_pin', 27))
        self.buzz_num = int (self.configDict.get ('buzz_num', 2))
        self.buzz_len = float (self.configDict.get ('buzz_len', 0.1))
        self.buzz_period = float (self.configDict.get ('buzz_period', 0.2))
        self.buzzer=Train (PTSimpleGPIO.MODE_PULSES, self.buzz_pin, 0, self.buzz_len, (self.buzz_period - self.buzz_len), self.buzz_num,PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        print('Debug: passed buzzer')
        #Speaker Settings == Buzzer
        self.speakerPin=int(self.configDict.get ('speaker_pin', 25))
        self.speakerFreq=float(self.configDict.get ('speaker_freq', 6000))
        self.speakerDuty = float(self.configDict.get ('speaker_duty', 0.5))
        self.speakerOffForReward = float(self.configDict.get ('speaker_OffForReward', 1.5))
        self.speaker=Infinite_train (PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        print('Debug: passed speaker')
        '''

        #Stepper motor settings
        #Shift register controlled by 4 GPIOs
        self.DS = int(self.settingsDict.get('DS', 4))
        self.Q7S = int(self.settingsDict.get('Q7S', 6))
        self.SHCP = int(self.settingsDict.get('SHCP', 5))
        self.STCP = int(self.settingsDict.get('STCP', 17))

        self.delay = self.settingsDict.get('motor_delay', 0.03)

        GPIO.setup(self.SHCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.DS, GPIO.OUT, initial = GPIO.LOW)
        GPIO.setup(self.STCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.Q7S, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

        self.mot_q = Queue(maxsize=0) #Queues stepper motor commands
        self.phase_queue = Queue(maxsize=0) #Returns the new phase of the motors during the matching
        self.phase = np.array([0,0])
        self.pos = np.array([0,0])
        self.laser_points = []
        self.image_points = []
        # Define boundaries to exclude unrealistic image registration results
        self.max_trans = 60
        self.max_scale = np.array([0.9,1.1])
        self.max_angle = 15
        '''
        Info: New stepper commands are queued (self.mot_q) and processed on
        another processor.
        Main program keeps track of the phase of the stepper motors and queues
        (self.phase_queue) the recent phase to make it available for the another
        processor.
        '''
        self.hdf_path = '/home/pi/Documents/' + self.settingsDict.get('hdf_path')
        #Experiment settings
        #self.headFixTime = float (self.settingsDict.get ('headFixTime', 30))
        #self.lickWithholdTime = float (self.settingsDict.get ('lickWithholdTime', 1))
        #self.afterStimWithholdTime = float(self.settingsDict.get ('after_Stim_Withhold_Time', 0.2))
        super().setup()
        # self.rewardInterval = float (self.settingsDict.get ('rewardInterval', 2))
        # self.nRewards = int (self.settingsDict.get('nRewards', 2))

        #Mouse scores
        #self.buzzTimes = []
        #self.buzzTypes = []
        #self.lickWithholdTimes = []
        self.rewardTimes = []

    def trialPrep(self):
        return self.align()

    def stimulate (self):
        self.pulse(self.laser_on_time, self.duty_cycle)

    def trialEnd(self):
        #Move laser back to zero position at the end of the trial
        self.camera.stop_preview()
        self.move_to(np.array([0,0]),topleft=True,join=False)

#============== Utility functions for the stepper motors and laser =================

    def unlock(self):
        #De-energize the motors by toggling 0 into all shift registers
        GPIO.output(self.DS,0)
        for i in range(8):
            GPIO.output(self.SHCP,0)
            GPIO.output(self.SHCP,1)
        GPIO.output(self.STCP,0)
        GPIO.output(self.STCP,1)

    def feed_byte(self,byte):
        #Toggle a byte into the shjft registers
        for j in reversed(byte):
            GPIO.output(self.DS,j)
            GPIO.output(self.SHCP,0)
            GPIO.output(self.SHCP,1)
        GPIO.output(self.STCP,0)
        GPIO.output(self.STCP,1)

    def get_state(self):
        # Read out serial output and store state. Feed state back into shift reg.
        # Create empty array to store the state
        state = np.empty(8,dtype=int)
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

    def get_arrow_dir(self,key):
        # return direction of stepper motor step and cross-hair step.
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
        # Callback function, which responds to keyboard strokes.
        di = self.get_arrow_dir(key)
        if any(np.asarray(di[:2])!=0):
            self.mot_q.put(di[:2]) #Queue the motor command
            self.pos += np.asarray(di[:2]) #Update the motor position
        if any(np.asarray(di[2:])!=0):
            self.cross_q.put(di[2:]) #Queue the cross-hair
        if key == keyboard.Key.space:
            self.kb.press(keyboard.Key.backspace)
            self.kb.release(keyboard.Key.backspace)
            self.image_points.append(np.copy(self.cross_pos))
            self.laser_points.append(np.copy(np.flip(self.pos,axis=0)))
            print('\n\nPosition saved!\n\n')
        if key == keyboard.Key.esc:
            if len(self.image_points)>=3:
                self.image_points = np.asarray(self.image_points)
                self.laser_points = np.asarray(self.laser_points)
                try:
                    self.cross_q.task_done()
                    self.phase_q.task_done()
                    self.cross_q.put(None) #To terminate the thread
                except:
                    pass
                # Stop listener
                return False
            else:
                print('\n\nNeed at least 3 points!\n\n')
                pass

    def make_cross(self):
        #Define a simple cross-hair and add it as an overlay to the preview
        cross = np.zeros((self.overlay_resolution[0],self.overlay_resolution[0],3),dtype=np.uint8)
        cross[self.cross_pos[0],:,:] = 0xff
        cross[:,self.cross_pos[1],:] = 0xff
        self.l3 = self.camera.add_overlay(cross.tobytes(),
                            layer=3,
                            alpha=100)

    def update_cross(self,q):
        #Callback function, which processes changes in the cross-hair position.
        while True:
            #Repeatedly check wether queue has something to process
            if not q.empty():
                prod = q.get()
                if prod is None:
                    return False
                next_pos = self.cross_pos + np.array(prod)
                #Make sure the cross remains within the boundaries given by the overlay
                if not any((any(next_pos<0),any(next_pos>=np.array(self.overlay_resolution)))):
                    self.cross_pos = next_pos
                    self.camera.remove_overlay(self.l3)
                    self.make_cross()
                else:
                    pass

    def update_mot(self,mot_q,phase_queue,delay,topleft):
        #Callback funtion to process new motor steps. Runs on a different processor.
        while True:
            if not mot_q.empty():
                x,y = mot_q.get()
                self.move(x,y,phase_queue,delay,topleft,mp=True)
                self.phase += np.array([x,y])
                self.phase = self.phase%8
                self.pos += np.array([x,y])


    def move(self,x,y,phase,delay,topleft,mp):
        #Main function, which moves stepper motors by x and y.
        if mp == True:
            phase_x,phase_y = phase.get()
        else:
            phase_x,phase_y = phase

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
        if mp == True:
            #Save the phase
            phase.put([phase_x,phase_y])

    def move_to(self,new_pos,topleft=True,join=False):
        #High-level function, which invokes self.move to run on another processor
        steps = np.around(new_pos).astype(int)-self.pos
        mp = Process(target=self.move, args=(steps[0],steps[1],self.phase,self.delay,topleft,False,))
        mp.daemon = True
        mp.start()
        if join:
            timeout = 30
            start = time()
            while time() - start <= timeout:
                if mp.is_alive():
                    sleep(0.1)
                else:
                    break
            else:
                print('Process timed out, killing it!')
                mp.terminate()
                mp.join(timeout=1.0)
            #mp.join()
        #Calculate next phase
        self.phase += steps%8
        self.phase = self.phase%8
        self.pos += steps

    def pulse(self,duration,duty_cycle=0):
        if duration<=1000:
            for i in range(len(self.array)):
                self.array[i] = 0
            for i in range(1,duration):
                self.array[i]=duty_cycle
            self.PWM.start_train()
        else:
            print('Duration must be below 1000 ms.')


#==== High-level Utility functions: Matching of coord systems, target selection and image registration ====

    def matcher(self):
        #GUI to select three points using the matching aid tool.

        print('\nINSTRUCTION\n')
        print('Move:\tLaser\t\tcross hairs')
        print('---------------------------------------')
        print('Keys:\tarrow keys\tdelete home end page-down\n')
        print('1.: Move the laser and the cross hairs to at least 3 different points and hit the space key to save a point.')
        print('2.: To exit, hit the esc key.\n\n')

        self.laser_points = []
        self.image_points = []

        try:
            #Turn on the laser
            self.pulse(1000,self.duty_cycle) #If duration = 1000, laser stays on.
            #Start camera preview
            self.camera.start_preview()

            self.make_cross()
            #Start the thread which updates the cross
            t = Thread(target = self.update_cross,args=(self.cross_q,))
            t.setDaemon(True)
            t.start()

            #Start the process which updates the motor
            while not self.phase_queue.empty():
                self.phase_queue.get()
            self.phase_queue.put(self.phase)
            mp = Process(target=self.update_mot, args=(self.mot_q,self.phase_queue,self.delay,False,))
            mp.daemon = True
            mp.start()

            #Make object for the keyboard Controller
            self.kb = keyboard.Controller()

            #Start the thread which listens to the keyboard
            with keyboard.Listener(on_press=self.on_press) as k_listener:
                k_listener.join()
        finally:
            self.move_to(np.array([0,0]),topleft=True,join=False)
            k_listener.stop()
            mp.terminate() #not necessary
            mp.join(timeout=1.0)
            #Turn off the laser
            self.pulse(0)
            self.camera.stop_preview()
            self.camera.remove_overlay(self.l3)
            self.l3.close()


        #======================Calculation================================

        def solver(image_points,laser_points):
            #Takes 3 points defined in laser- and image-coordinates and returns the coefficient matrix
            a=np.column_stack((image_points,np.array([1,1,1])))
            b1=laser_points[:,0]
            b2=laser_points[:,1]
            return np.vstack((np.linalg.solve(a, b1),np.linalg.solve(a, b2)))
        #I don't know why this has to be here, but it does
        print(self.laser_points)
        #Average the coefficient matrix obatained by solving all combinations of triplets.
        if len(list(set([x[0] for x in self.laser_points])))>=3:
            self.coeff = []
            for i in combinations(enumerate(zip(self.image_points,self.laser_points)),3):
                ip = np.vstack((i[0][1][0],i[1][1][0],i[2][1][0]))
                lp = np.array([i[0][1][1],i[1][1][1],i[2][1][1]])
                self.coeff.append(solver(ip, lp))
            self.coeff = np.mean(np.asarray(self.coeff),axis=0)
        print("Center in laser coords:", np.dot(self.coeff, np.asarray([128, 128, 1])))

    def get_ref_im(self):
        #Save a reference image whithin the mouse object
        self.mouse.update({'ref_im' : np.empty((self.camera.resolution()[0], self.camera.resolution()[1], 3),dtype=np.uint8)})
        self.mouse.update({'timestamp': time()})
        self.camera.capture(self.mouse.get('ref_im'),'rgb')

    def select_targets(self):
        if(path.exists(self.hdf_path)):
            with File(self.hdf_path, 'r+') as hdf:
                for tag, mouse in hdf.items():
                    tempMouse = self.task.Subjects.get(tag)
                    if(mouse.__contains__('targets')):
                        tempMouse.update({'targets': mouse['targets'][:]})
                    if(mouse.__contains__('ref_im')):
                        tempMouse.update({'ref_im': mouse['ref_im'][:]})
        mice = self.task.Subjects.get_all()
        #GUI function for the selecting targets
        def manual_annot(img):
            warnings.filterwarnings("ignore",".*GUI is implemented.*")
            fig = plt.figure(figsize=(10,10))
            imgplot = plt.imshow(img)
            plt.title('Choose targets')
            plt.show(block=False)
            points = np.around(np.asarray(plt.ginput(n=1,show_clicks=True,timeout=0)))
            plt.close()
            return [int(points[0][1]),int(points[0][0])]

        if not hasattr(self,'coeff'):
            print('Need to perform the matching first before selecting targets')
            return None
        else:
            for tag, mouse in mice.items():
                if 'targets' in mouse:
                    inputStr = input('Certain/All mice already have brain targets.\n0: Select targets for remaining mice\n1: Select targets for all registered mice.\n')
                    break
                else:
                    inputStr = str(1)
            if inputStr == str(0):
                for tag, mouse in mice.items():
                    if ( 'targets' not in mouse and 'ref_im' in mouse):
                        print('Mouse: ', tag)
                        targets_coords = manual_annot(mouse.get('ref_im'))
                        mouse.update({'targets': np.asarray(targets_coords).astype(int)})
                        print('TARGET\tx\ty')
                        print('{0}\t{1}\t{2}'.format('0',mouse.get('targets')[0],mouse.get('targets')[1]))
            if inputStr == str(1):
                for tag, mouse in mice.items():
                    if 'ref_im' in mouse:
                        print('Mouse: ', tag)
                        targets_coords = manual_annot(mouse.get('ref_im'))
                        mouse.update({'targets': np.asarray(targets_coords).astype(int)})
                        print('TARGET\tx\ty')
                        print('{0}\t{1}\t{2}'.format('0',mouse.get('targets')[0],mouse.get('targets')[1]))
            with File(self.hdf_path, 'r+') as hdf:
                for tag, mouse in hdf.items():
                    tempMouse = self.task.Subjects.get(tag)
                    if 'targets' in tempMouse:
                        del mouse['targets']
                        mouse.require_dataset('targets',shape=(2,),dtype=np.uint8,data=tempMouse.get('targets'))
    def image_registration(self):
        #Runs at the beginning of a new trial
        def trans_mat(angle,x,y,scale):
            #Utility function to get the transformation matrix
            angle = -1*np.radians(angle)
            scale = 1/scale
            x = -1*x
            y = -1*y
            rot_ext = np.array([[np.cos(angle),-np.sin(angle),y*np.cos(angle)-x*np.sin(angle)],
                                [np.sin(angle),np.cos(angle),y*np.sin(angle)+x*np.cos(angle)]])
            scale_mat = np.array([[scale,1,1],[1,scale,1]])
            return rot_ext*scale_mat

        self.mouse.update({'trial_image' : np.empty((self.camera.resolution()[0], self.camera.resolution()[1], 3),dtype=np.uint8)})
        self.camera.capture(self.mouse.get('trial_image'),'rgb')
        timestamp = time()
        self.mouse.update({'trial_name': "M" + str(self.tag % 10000) + '_' + str(timestamp)})
        self.task.DataLogger.writeToLogFile (self.tag, 'Image', {'name': self.mouse.get('trial_name'), 'type': 'trial', 'reference': self.mouse.get('ref_name')}, timestamp)
        #Image registration
        #IMPROVE: Could run the registration on a different processor
        warnings.filterwarnings("ignore",".*the returned array has changed*")
        tf = ird.similarity(self.mouse.get('ref_im')[:,:,1],self.mouse.get('trial_image')[:,:,1],numiter=3)
        print('scale\tangle\tty\ttx')
        print('{0:.3}\t{1:.3}\t{2:.3}\t{3:.3}'.format(tf['scale'],tf['angle'],tf['tvec'][0],tf['tvec'][1]))
        #Check if results of image registration don't cross boundaries
        if all((abs(tf['angle'])<=self.max_angle,all(np.abs(tf['tvec'])<=self.max_trans),self.max_scale[0]<=tf['scale']<=self.max_scale[1])):
            #Transform the target to new position
            self.R = trans_mat(tf['angle'],tf['tvec'][1],tf['tvec'][0],tf['scale'])
            cent_targ = self.mouse.get('targets') - np.array([int(self.camera.resolution()[0]/2),int(self.camera.resolution()[0]/2)]) #translate targets to center of image
            trans_coord = np.dot(self.R,np.append(cent_targ,1))+np.array([int(self.camera.resolution()[0]/2),int(self.camera.resolution()[0]/2)])
            targ_pos = np.dot(self.coeff,np.append(trans_coord,1))
            print('TARGET\ttx\tty')
            print('{0}\t{1:.01f}\t{2:.01f}'.format('0',trans_coord[0],trans_coord[1]))
            self.task.DataLogger.writeToLogFile(self.tag, 'ImageRegistration', {'scale': tf['scale'], 'angle': tf['angle'], 'trans_x': tf['tvec'][0], 'trans_y': tf['tvec'][1]}, time())
            return targ_pos
        else:
            print('No laser stimulation: Image registration failed.')
            self.task.DataLogger.writeToLogFile (self.tag, 'ImageRegFail', None, time())
            return None


#=================Main functions called from outside===========================
    def align(self, resultsDict = {}, settingsDict = {}):
        """
        Aligns laser with reference image and assigned targets.
        Returns True if aligned successfully, False otherwise.
        """
        self.tag = self.task.tag
        self.mouse = self.task.Subjects.get(self.tag)
        self.loadH5()
        self.rewardTimes = []
        saved_targ_pos = None
        if not 'ref_im' in self.mouse or self.mouse.get('ref_im') is None:
            print('Take reference image')
            self.get_ref_im()
            timestamp = time()
            self.mouse.update({'ref_name': "M" + str(self.tag % 10000) + '_' + str(timestamp) + '_R'})
            self.mouse.update({'trial_name': "M" + str(self.tag % 10000) + '_' + str(timestamp) + '_R'})
            self.mouse.update({'trial_image': self.mouse.get('ref_im')})
            self.task.DataLogger.writeToLogFile (self.tag, 'ReferenceImage', {'name': self.mouse.get('ref_name')}, timestamp)
            self.h5updater()
            self.mouse.pop('ref_im')
            return False
        elif not 'targets' in self.mouse:
            print('Select targets')
            self.task.DataLogger.writeToLogFile(self.tag, 'TargetError', {'type': 'no targets selected'}, time())
            #If targets haven't been choosen -> release mouse again
            return False
        elif self.coeff is None:
            print("Match laser and camera coordinates")
            return False
        try:
            # Run this only if headfixed
            # self.rewarder.giveReward('task')
            print('Image registration')
            # ref_path = self.cageSettings.dataPath+'sample_im/'+datetime.fromtimestamp (int (time())).isoformat ('-')+'_'+str(self.mouse.tag)+'.jpg'
            self.mouse.update({'timestamp': time()})
            # self.camera.capture(ref_path)
            targ_pos = self.image_registration()
            # self.rewarder.giveReward('task')
            if targ_pos is None and saved_targ_pos is not None:
                targ_pos = saved_targ_pos
            if targ_pos is not None:
                saved_targ_pos = targ_pos
                print('Moving laser to target and capture image to assert correct laser position')
                self.move_to(np.flipud(targ_pos),topleft=True,join=True) #Move laser to target and wait until target reached
                self.mouse.update({'laser_spot': np.empty((self.camera.resolution()[0], self.camera.resolution()[1], 3),dtype=np.uint8)})
                self.pulse(self.laser_on_time,self.duty_cycle) #At least 60 ms needed to capture laser spot
                self.camera.capture(self.mouse.get('laser_spot'),'rgb', video_port=True)
                timestamp = time()
                self.mouse.update({'laser_name': "M" + str(self.tag % 10000) + '_' + str(timestamp) + '_LS'})
                self.task.DataLogger.writeToLogFile (self.tag, 'Stimulus', {'image_name': self.mouse.get('laser_name'), 'type': 'LaserSpot', 'coeff_matrix': self.coeff, 'duty_cycle': self.duty_cycle, "laser_on_time": self.laser_on_time, 'laser_targets': targ_pos, 'intended_targets': self.mouse.get('targets'), 'reference': self.mouse.get('ref_name')}, timestamp)
                sleep(0.1)
            # # Repeatedly give a reward and pulse simultaneously
            # timeInterval = self.rewardInterval # - self.rewarder.rewardDict.get ('task')
            # self.rewardTimes = []
            # self.camera.start_preview()
            # for reward in range(self.nRewards):
            #     self.rewardTimes.append (time())
            #     if targ_pos is not None:
            #         self.pulse(self.laser_on_time,self.duty_cycle)
            #         self.task.DataLogger.writeToLogFile (self.tag, 'LaserPulse', None, time())
            #     self.rewarder.giveReward('task')
            #     sleep(timeInterval)
            # newRewards = resultsDict.get('rewards', 0) + self.nRewards
            # resultsDict.update({'rewards': newRewards})
            # self.camera.stop_preview()
        except Exception as e:
            print(str(e))
            return False
        finally:
            self.h5updater()
            self.mouse.pop('ref_im', None)
            self.mouse.pop('trial_image', None)
            self.mouse.pop('trial_name', None)
            self.mouse.pop('laser_spot', None)
            self.mouse.pop('laser_name', None)
            #Move laser back to zero position at the end of the trial
            # self.move_to(np.array([0,0]),topleft=True,join=False)
            return True


    def hardwareTest(self):
        #Tester function called from the hardwareTester. Includes Stimulator
        #specific hardware tester.
        while(True):
            inputStr = input ('r=reference image, m= matching, t= targets, a = accuracy, v = vib. motor, p= laser tester, c= motor check, a= camera/LED, s= speaker, q= quit: ')
            if inputStr == 'm':
                self.matcher()
                self.settingsDict.update({'coeff_matrix' : self.coeff.tolist()})
            elif inputStr == 'r':
                self.editReference()
            elif inputStr == 't':
                self.select_targets()
            elif inputStr == "a":
                self.accuracyTest()
            elif inputStr == 'p':
                self.camera.start_preview()
                self.pulse(1000,self.duty_cycle)
                input ('adjust Laser: Press any key to quit ')
                self.camera.stop_preview()
                self.pulse(0)
            elif inputStr == 'a':
                #Display preview and turn on LED
                self.camera.start_preview()
                self.task.BrainLight.onForStim()
                input ('adjust camera/LED: Press any key to quit ')
                self.camera.stop_preview()
                self.task.BrainLight.offForStim()
            elif inputStr == 's':
                self.speaker.start_train()
                sleep(3)
                self.speaker.stop_train()
            elif inputStr == 'v':
                self.buzzer.do_train()
            elif inputStr == 'c':
                self.move_to(np.array([0,0]),topleft=True,join=False)
            elif inputStr == 'q':
                break

    def accuracyTest(self):
        """
        For the given coefficient matrix, moves the laser to the center, then takes an image.
        Then, moves to 100 random points, and then back to center, taking another image.
        These images can then be compared to determine the long-term accuracy of the stepper motors.
        """
        continueStr = input("This may take a while. Are you sure? (Y/N)")
        if continueStr.lower() == "y":
            self.camera.start_preview()
            self.pulse(1000,self.duty_cycle)
            print("Center in laser coords:", np.dot(self.coeff, np.asarray([128, 128, 1])))
            self.move_to(np.flipud(np.dot(self.coeff, np.asarray([128, 128, 1]))), topleft=True,join=True)
            self.accuracyStart = np.empty((self.camera.resolution()[0], self.camera.resolution()[1], 3),dtype=np.uint8)
            self.camera.stop_preview()
            self.camera.capture(self.accuracyStart,'rgb')
            self.pulse(0)
            for i in range (0, 100):
                x = randrange(0, 256)
                y = randrange(0, 256)
                self.move_to(np.flipud(np.dot(self.coeff, np.asarray([x, y, 1]))), topleft=True,join=True)
            print("Completed, moving to center.")
            self.camera.start_preview()
            self.pulse(1000,self.duty_cycle)
            self.move_to(np.flipud(np.dot(self.coeff, np.asarray([128, 128, 1]))), topleft=True,join=True)
            self.accuracyEnd = np.empty((self.camera.resolution()[0], self.camera.resolution()[1], 3),dtype=np.uint8)
            self.camera.stop_preview()
            self.camera.capture(self.accuracyEnd,'rgb')
            self.pulse(0)
            if(path.exists(self.hdf_path)):
                with File(self.hdf_path, 'r+') as hdf:
                    folder = hdf.require_group("accuracy")
                    if folder.__contains__('start'):
                        del folder['start']
                    if folder.__contains__('end'):
                        del folder['end']
                    resolution_shape = ( self.camera.resolution()[0], self.camera.resolution()[1], 3) #rgb layers
                    ref = folder.require_dataset('start',shape=tuple(resolution_shape),dtype=np.uint8,data=self.accuracyStart)
                    ref.attrs.modify('CLASS', np.string_('IMAGE'))
                    ref.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
                    ref.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
                    ref.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
                    ref.attrs.modify('IMAGE_MINMAXRANGE', [0,255])
                    ref = folder.require_dataset('end',shape=tuple(resolution_shape),dtype=np.uint8,data=self.accuracyEnd)
                    ref.attrs.modify('CLASS', np.string_('IMAGE'))
                    ref.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
                    ref.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
                    ref.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
                    ref.attrs.modify('IMAGE_MINMAXRANGE', [0,255])

    def setdown (self):
        #Remove portions saved in h5
        super().setdown()

    def loadH5 (self):

        if(path.exists(self.hdf_path)):
            with File(self.hdf_path, 'r+') as hdf:
                for tag, mouse in hdf.items():
                    if str(tag) == str(self.tag):
                        if(mouse.__contains__('ref_im')):
                            self.mouse.update({'ref_im' : mouse['ref_im'][:]})
                            attrs = mouse['ref_im'].attrs
                            self.mouse.update({'ref_name': attrs.get('NAME')})
                        if(mouse.__contains__('targets')):
                            self.mouse.update({'targets': mouse['targets'][:]})
        else:
            with File(self.hdf_path, 'w') as hdf:
                pass
    def editReference (self):
        tag = ""
        if(path.exists(self.hdf_path)):
            with File(self.hdf_path, 'r+') as hdf:
                while (not hdf.__contains__(tag) and tag != "e"):
                    print('Select a Mouse to edit: (e to exit)', hdf.keys())
                    tag = input('Mouse tag: ')
                if(tag != 'e'):
                    mouse = hdf[tag]
                    nextInput = ""
                    fig = plt.figure(figsize=(10,10))
                    img = mouse['ref_im'][:]
                    imgplot = plt.imshow(img)
                    plt.title('Reference Image (click to hide)')
                    plt.show(block=False)
                    plt.ginput(n=1,show_clicks=False,timeout=0)
                    while nextInput.lower() != "n" and nextInput.lower() != "y":
                        nextInput = input('Delete reference image? (Y/N):')
                    if(nextInput.lower() == "y"):
                        del mouse['ref_im']
                        nextInput = ""
                        confirm = False
                        self.task.DataLogger.writeToLogFile(int(tag), "ReferenceDelete", None, time())
                        while( not confirm):
                            while (not mouse['trial_image'].__contains__(nextInput) and nextInput != "n"):
                                print('Select a new reference image: (n for no image) ', mouse['trial_image'].keys())
                                nextInput = input('Image: ')
                            if(nextInput.lower() != 'n'):
                                fig = plt.figure(figsize=(10,10))
                                img = mouse['trial_image/' + nextInput][:]
                                imgplot = plt.imshow(img)
                                plt.title('Selected (click to hide):')
                                plt.show(block=False)
                                plt.ginput(n=1,show_clicks=False,timeout=0)
                                plt.close()
                                conf = input('Use this? (Y/N)')
                                if(conf.lower() == 'y'):
                                    confirm = True
                            else:
                                confirm = True
                        if(nextInput.lower() != 'n'):
                            mouse['ref_im'] = mouse['trial_image/' + nextInput]
                            self.task.DataLogger.writeToLogFile(int(tag), "ReferenceImage", {'name': nextInput}, time())





    def h5updater (self):
        with File(self.hdf_path, 'r+') as hdf:
            mouse = hdf.require_group(str(self.tag))
            resolution_shape = ( self.camera.resolution()[0], self.camera.resolution()[1], 3) #rgb layers
            if 'ref_im' in self.mouse:
                ref = mouse.require_dataset('ref_im',shape=tuple(resolution_shape),dtype=np.uint8,data=self.mouse.get('ref_im'))
                ref.attrs.modify('CLASS', np.string_('IMAGE'))
                ref.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
                ref.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
                ref.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
                ref.attrs.modify('IMAGE_MINMAXRANGE', [0,255])
                ref.attrs.modify('NAME', np.string_(self.mouse.get('ref_name')))
            if 'targets' in self.mouse:
                mouse.require_dataset('targets',shape=(2,),dtype=np.uint8,data=self.mouse.get('targets'))
            t = mouse.require_group('trial_image')
            if 'trial_image' in self.mouse:
                tr = t.require_dataset(self.mouse.get('trial_name'),shape=tuple(resolution_shape),dtype=np.uint8,data=self.mouse.get('trial_image'))
                tr.attrs.modify('CLASS', np.string_('IMAGE'))
                tr.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
                tr.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
                tr.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
                tr.attrs.modify('IMAGE_MINMAXRANGE', [0,255])
                tr.attrs.modify('timestamp', self.mouse.get('timestamp'))
            if 'laser_spot' in self.mouse:
                ls = t.require_dataset(self.mouse.get('laser_name') +'_laser_spot',shape=tuple(resolution_shape),dtype=np.uint8,data=self.mouse.get('laser_spot'))
                ls.attrs.modify('CLASS', np.string_('IMAGE'))
                ls.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
                ls.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
                ls.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
                ls.attrs.modify('IMAGE_MINMAXRANGE', [0,255])
                ls.attrs.modify('timestamp', self.mouse.get('timestamp'))
