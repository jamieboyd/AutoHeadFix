from AHF_Stimulator_Rewards import AHF_Stimulator_Rewards
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse, Mice
import RPi.GPIO as GPIO
from AHF_Camera import AHF_Camera
from time import sleep
import numpy as np
from array import array
from PTPWM import PTPWM
import imreg_dft as ird
from pynput import keyboard

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

class AHF_Stimulator_Laser (AHF_Stimulator_Rewards):
    def __init__ (self, configDict, rewarder, lickDetector, textfp):
        super().__init__(configDict, rewarder, lickDetector, textfp)
        self.setup()

    @staticmethod
    def dict_from_user (stimDict):
        if not 'DS' in stimDict:
            stimDict.update({'DS' : 4})
        if not 'Q7S' in stimDict:
            stimDict.update({'Q7S' : 6})
        if not 'SHCP' in stimDict:
            stimDict.update({'SHCP' : 5})
        if not 'STCP' in stimDict:
            stimDict.update({'STCP' : 17})
        if not 'duty_cycle' in stimDict:
            stimDict.update({'duty_cycle' : 80})
        if not 'laser_on_time' in stimDict:
            stimDict.update({'laser_on_time' : 0.5})
        if not 'PWM_mode' in stimDict:
            stimDict.update({'PWM_mode'} : 0)
        if not 'PWM_channel' in stimDict:
            stimDict.update({'PWM_channel' : 1})
        return super(AHF_Stimulator_Laser,AHF_Stimulator_Laser).dict_from_user (stimDict)

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
        self.camera = AHF_Camera(expSettings.camParamsDict)

        GPIO.setup(self.SHCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.DS, GPIO.OUT, initial = GPIO.LOW)
        GPIO.setup(self.STCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.Q7S, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

        self.pos = np.array([0,0])
        self.phase_x = 0
        self.phase_y = 0
        self.laser_points = []
        self.image_points = []
'''
===================== Utility functions for the stepper motors =================
'''
    def unlock(self):
        GPIO.output(self.DS,0)
        for i in range(8):
            GPIO.output(self.SHCP,0)
            GPIO.output(self.SHCP,1)
        GPIO.output(self.STCP,0)
        GPIO.output(self.STCP,1)
        print('Motors unlocked.')

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

    @staticmethod
    def get_dir(steps):
        if steps > 0:
            return 1
        elif steps < 0:
            return -1
        else:
            return 0

    @staticmethod
    def get_arrow_dir(key):
        if key == keyboard.Key.right:
            return 1,0
        elif key == keyboard.Key.left:
            return -1,0
        elif key == keyboard.Key.down:
            return 0,1
        elif key == keyboard.Key.up:
            return 0,-1
        else:
            pass

    def on_press(self,key):
        try:
            di = get_arrow_dir(key)
            self.move(di[0],di[1])
        except:
            pass

    def on_release(self,key):
        if key == keyboard.Key.esc:
            # Stop listener
            return False
        if key == keyboard.Key.enter:
            self.laser_points.append(self.pos)
            self.ref = np.empty((width,height,3),dtype=np.uint8)
            self.camera.capture(self.ref,'rgb')
            print('Reference point saved')
        else:
            pass

    def move(self,x,y,delay=0.03):
        states = [[1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
                  [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1]]

        if abs(x)>=abs(y):
            x_steps = np.arange(start=0,stop=abs(x),dtype=int)
            #y_steps = np.arange(start=0,stop=abs(y),dtype=int)
            y_steps = np.linspace(start=0,stop=abs(x-1),num=abs(y),endpoint=False,dtype=int)
        else:
            y_steps = np.arange(start=0,stop=abs(y),dtype=int)
            #x_steps = np.arange(start=0,stop=abs(x),dtype=int)
            x_steps = np.linspace(start=0,stop=abs(y-1),num=abs(x),endpoint=False,dtype=int)

        for i in (i for i in x_steps if x_steps.size>=y_steps.size):
            next_phase_x = (self.phase_x + self.get_dir(x)) % len(states)
            if i in y_steps:
                next_phase_y = (self.phase_y + self.get_dir(y)) % len(states)
                byte = states[next_phase_x]+states[next_phase_y]
                self.phase_y = next_phase_y
            else:
                state_y = self.get_state()[-4:]
                byte = states[next_phase_x]+state_y
            #Send and execute new byte
            self.feed_byte(byte)
            #Update phase
            self.phase_x = next_phase_x
            sleep(delay)

        for i in (i for i in y_steps if y_steps.size>x_steps.size):
            next_phase_y = (self.phase_y + self.get_dir(y)) % len(states)
            if i in x_steps:
                next_phase_x = (self.phase_x + self.get_dir(x)) % len(states)
                byte = states[next_phase_x]+states[next_phase_y]
                self.phase_x = next_phase_x
            else:
                state_x = self.get_state()[:4]
                byte = state_x+states[next_phase_y]
            #Send and execute new byte
            self.feed_byte(byte)
            self.phase_y = next_phase_y
            sleep(delay)

        #Update the position
        self.pos += np.array([x,y])

    def move_to(self, new_x, new_y,delay=0.03,topleft=True):
        steps_x = int(round(new_x)) - self.pos[0]
        steps_y = int(round(new_y)) - self.pos[1]
        if topleft==True:
            self.move(steps_x-30, steps_y-30,delay)
            sleep(0.03)
            self.move(30,30,delay)
        else:
            self.move(steps_x, steps_y,delay)
'''
===================== Utility functions for the laser =========================
'''
    def pulse(self,duration,duty_cycle):
        if duration<=1000:
            #self.array = array('i',[int(duty_cycle*10) if i<duration else 0 for i in range(1000)])
            #might change this to enumerate
            for i in self.array:
                i = 0
            for i in range(1,duration):
                self.array[i]=duty_cycle
            self.PWM.start_train()
        else:
            print('Duration must be below 1000 ms.')
'''
========================Utility functions for the matching=====================
'''
    @staticmethod
    def trans_mat(angle,x,y,scale):
        rot_ext = np.array([[np.cos(angle),-np.sin(angle),x],
                            [np.sin(angle),np.cos(angle),y]])
        scale_mat = np.array([[1/scale[0],1,1],[1,1/scale[1],1]])
        return rot_ext*scale_mat

    @staticmethod
    def dft_trans_mat(angle,x,y,scale):
        angle = -1*np.radians(angle)
        scale = 1/scale
        x = -1*x
        y = -1*y
        rot_ext = np.array([[np.cos(angle),-np.sin(angle),y*np.cos(angle)-x*np.sin(angle)],
                            [np.sin(angle),np.cos(angle),y*np.sin(angle)+x*np.cos(angle)]])
        scale_mat = np.array([[scale,1,1],[1,scale,1]])
        return rot_ext*scale_mat

    @staticmethod
    def manual_annot(img):
        fig = plt.figure(figsize=(22,12))
        imgplot = plt.imshow(img[:,:,1],'gray')
        plt.title('Click on laser spot.')
        plt.show()
        points = np.around(np.asarray(plt.ginput(n=1,show_clicks=True)))
        plt.close()
        #fig = plt.figure(figsize=(22,12))
        xses = map(int,[t[0] for t in points])
        yses = map(int,[t[1] for t in points])
        return list(xses[0]),list(yses[0])

    def matcher(self):
        #Reset clocks and zero serial input
        self.unlock()
        #Turn on the laser
        self.pulse(1000,80) #If duration = 1000 Laser stays on.
        #Start camera preview
        self.camera.start_preview(fullscreen = False, window=camera.AHFpreview)
        # Collect events until released
        print('Use the arrow keys to move the laser to two reference points and \
        hit the enter key. When done, hit the esc key.')
        with keyboard.Listener(
                on_press=on_press,
                on_release=on_release) as listener:
            while True:
                if hasattr(self,'ref'):
                    self.image_points = manual_annot(self.ref)
                    del self.ref
                else:
                    pass

'''
==============================Trial=============================================
'''
    def run(thisMouse, expSettings, cageSettings, camera, rewarder, headFixer, stimulator, UDPTrigger=None):
        #run matcher


        #Wait for mouse, when mouse inside (RFID tag) for the first time, make object and take image and let user select brain targets
        # Run stimulation, for now without reward and stuff

    def logfile:


if __name__ == '__main__':
