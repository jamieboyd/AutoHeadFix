from AHF_Stimulator_Rewards import AHF_Stimulator_Rewards
from AHF_Rewarder import AHF_Rewarder
from AHF_Mouse import Mouse, Mice
import RPi.GPIO as GPIO
from AHF_Camera import AHF_Camera
from picamera import PiCamera
from pynput import keyboard
from StepperController import StepperController
import numpy as np
from PTPWM import PTPWM
from array import array
from queue import Queue
from threading import Thread
from time import sleep
from itertools import combinations,product
import imreg_dft as ird
import matplotlib.pyplot as plt
import warnings

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
        if not 'width' in stimDict:
            stimDict.update({'width' : 200})
        if not 'height' in stimDict:
            stimDict.update({'height' : 200})
        if not 'preview_width' in stimDict:
            stimDict.update({'preview_width' : 600})
        if not 'preview_height' in stimDict:
            stimDict.update({'preview_height' : 600})
        if not 'preview_pos' in stimDict:
            stimDict.update({'preview_pos' : 50})
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
        #self.camera = AHF_Camera(expSettings.camParamsDict)
        self.width = int(self.configDict.get('width', 200))
        self.height = int(self.configDict.get('height', 200))
        self.preview_width = int(self.configDict.get('preview_width', 600))
        self.preview_height = int(self.configDict.get('preview_height', 600))
        self.preview_pos = int(self.configDict.get('preview_pos', 50))
        self.ratio = self.preview_width/self.width
        self.overlay_width,self.overlay_height = self.rounding(self.preview_width,self.preview_height)
        self.actual_width,self.actual_height = self.rounding(self.width,self.height)
        self.cross_pos = np.array([self.preview_height//2,self.preview_width//2])
        self.cross_step = int(self.preview_width/50)

        self.cross_q = Queue(maxsize=0)

        GPIO.setup(self.SHCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.DS, GPIO.OUT, initial = GPIO.LOW)
        GPIO.setup(self.STCP, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.Q7S, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

        self.phase_x = 0
        self.phase_y = 0
        self.pos = np.array([0,0])
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
            self.move(x=di[0],y=di[1])
        if any(np.asarray(di[2:])!=0):
            self.cross_q.put(di[2:])
        if key == keyboard.Key.space:
            self.image_points.append(np.copy(self.cross_pos/self.ratio))
            self.laser_points.append(np.copy(np.flip(self.pos,axis=0)))
            print('Position saved!')
        if key == keyboard.Key.esc:
            if len(self.image_points)>=3:
                self.image_points = np.asarray(self.image_points)
                self.laser_points = np.asarray(self.laser_points)
                # Stop listener
                return False
            else:
                print('Need at least 3 points!')
                print('Want to exit anyway? [y/n]')
                if input()=='y':
                    self.image_points = np.asarray(self.image_points)
                    self.laser_points = np.asarray(self.laser_points)
                    return False
                else:
                    pass

    def make_cross(self):
        cross = np.zeros((self.overlay_height,self.overlay_width,3),dtype=np.uint8)
        cross[self.cross_pos[0],:,:] = 0xff
        cross[:,self.cross_pos[1],:] = 0xff
        self.l3 = self.camera.add_overlay(cross.tobytes(),
                            layer=3,
                            alpha=100,
                            fullscreen=False,
                            window = (self.preview_pos,
                                      self.preview_pos,
                                      self.preview_width,
                                      self.preview_height))

    def update_cross(self,q):
        while True:
            if not q.empty():
                #Make sure the cross remains within the boundaries given by the overlay
                next_pos = self.cross_pos + np.array(q.get())
                if not any((any(next_pos<0),any(next_pos>=np.array([self.preview_height,self.preview_width])))):
                    self.cross_pos = next_pos
                    self.camera.remove_overlay(self.l3)
                    self.make_cross()
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
            for i in self.array:
                i = 0
            for i in range(1,duration):
                self.array[i]=duty_cycle
            self.PWM.start_train()
        else:
            print('Duration must be below 1000 ms.')


'''
==== Functions to perform the matching, target selection and image registration ====
'''    def matcher(self):
        '''
        ========================Solver function for the matching=====================
        '''
        def solver(image_points,laser_points):
            #===================Solver Approach 2===================
            a=np.column_stack((image_points,np.array([1,1,1])))
            b1=laser_points[:,0]
            b2=laser_points[:,1]
            return np.vstack((np.linalg.solve(a, b1),np.linalg.solve(a, b2)))

        print('\nINSTRUCTION\n')
        print('Move:\tLaser\t\tcross hairs')
        print('---------------------------------------')
        print('Keys:\tarrow keys\tdelete home end page-down\n')
        print('1.: Move the laser and the cross hairs to at least 3 different points and hit the space key.')
        print('2.: To exit, hit the esc key.')

        try:
            with PiCamera() as self.camera:
                #Turn on the laser
                self.pulse(1000,5) #If duration = 1000 Laser stays on.
                self.camera.resolution = (self.overlay_width,self.overlay_height)
                self.camera.framerate = 24
                #Start camera preview
                self.camera.start_preview(fullscreen = False, window = (self.preview_pos,
                                                                   self.preview_pos,
                                                                   self.preview_width,
                                                                   self.preview_height))

                self.make_cross()
                #Start the thread which updates the cross
                t = Thread(target = self.update_cross,args=(self.cross_q,))
                t.setDaemon(True)
                t.start()

                #Make object for the keyboard Controller
                self.kb = keyboard.Controller()

                #Start the thread which listens to the keyboard
                with keyboard.Listener(on_press=self.on_press) as k_listener:
                    k_listener.join()
        finally:
            try:
                self.cross_q.task_done()
            except:
                pass
            self.unlock()

        '''
        ======================Calcualtion================================
        Average the coefficient matrix obatained by solving all combinations of triplets.
        '''
        if self.image_points.shape[0] >= 3:
            self.coeff = []
            for i in combinations(enumerate(zip(self.image_points,self.laser_points)),3):
                ip = np.vstack((i[0][1][0],i[1][1][0],i[2][1][0]))
                lp = np.array([i[0][1][1],i[1][1][1],i[2][1][1]])
                self.coeff.append(solver(ip, lp))
            self.coeff = np.mean(np.asarray(self.coeff),axis=0)
        else:
            print('Need more than 3 points for the calcualtion.')
            return None

    def get_targets(self):
        '''
        ========================GUI function for the selecting targets=====================
        '''
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

        if self.image_points.shape[0] < 3:
            return None
        with PiCamera() as camera:
            self.targets = {}
            camera.resolution = (self.overlay_width,self.overlay_height)
            camera.framerate = 24
            target_image = np.empty((self.overlay_width * self.overlay_height * 3),dtype=np.uint8)
            camera.capture(target_image,'rgb')
            target_image = target_image.reshape((self.overlay_height,self.overlay_width,3))
            target_image = target_image[:self.preview_width,:self.preview_height,:]

            self.ref = np.empty((self.actual_height, self.actual_width, 3),dtype=np.uint8)
            warnings.filterwarnings("ignore",".*you may find the equivalent alpha format faster*")
            camera.capture(self.ref,'rgb',resize=(self.actual_width,self.actual_height))
            self.ref = self.ref[:self.width,:self.height,:]

            targets_coords = manual_annot(target_image)
            targets_coords = list(zip(np.array(targets_coords[0]),np.array(targets_coords[1])))

            for i,j in enumerate(targets_coords):
                target = 'target_'+str(i)
                self.targets[target]=np.array(np.asarray(j)/self.ratio).astype(int) #Scale coordinate to desired size

            print('TARGET\tx\ty')
            for key,value in self.targets.items():
                print('{0}\t{1}\t{2}'.format(key[-1],value[0],value[1]))

        try:
            self.pulse(1000,5)
            for key,value in self.targets.items():
                #======================Approach 1==========================
                #targ_pos = np.dot(aff_rotmat(self.rot,self.translation,self.scale,self.clockwise),np.append(np.asarray(value),1))
                targ_pos = np.dot(self.coeff,np.append(np.asarray(value),1))
                print('Moving to: ',targ_pos)
                self.move_to(targ_pos[1],targ_pos[0])
                sleep(2)
        finally:
            self.move_to(0,0)
            self.unlock()
            #Ugly way to turn the laser off
            #del self.PWM

    def next_trial(self):
        '''
        ============Utility function to get the rotation matrix=================
        '''
        def trans_mat(angle,x,y,scale):
            angle = -1*np.radians(angle)
            scale = 1/scale
            x = -1*x
            y = -1*y
            rot_ext = np.array([[np.cos(angle),-np.sin(angle),y*np.cos(angle)-x*np.sin(angle)],
                                [np.sin(angle),np.cos(angle),y*np.sin(angle)+x*np.cos(angle)]])
            scale_mat = np.array([[scale,1,1],[1,scale,1]])
            return rot_ext*scale_mat

        with PiCamera() as camera:
            camera.resolution = (self.actual_width,self.actual_height)
            camera.framerate = 24
            trial = np.empty((self.actual_width * self.actual_height * 3),dtype=np.uint8)
            camera.capture(trial,'rgb')
            trial = trial.reshape((self.actual_height,self.actual_width,3))
            trial = trial[:self.width,:self.height,:]
        try:
            warnings.filterwarnings("ignore",".*the returned array has changed*")
            tf = ird.similarity(self.ref[:,:,0],trial[:,:,0],numiter=3)
            print('scale\tangle\tty\ttx')
            print('{0:.3}\t{1:.3}\t{2:.3}\t{3:.3}'.format(tf['scale'],tf['angle'],tf['tvec'][0],tf['tvec'][1]))

            #Transform the reference targets
            R = trans_mat(tf['angle'],tf['tvec'][1],tf['tvec'][0],tf['scale'])
            print('TARGET\ttx\tty')
            for key,value in self.targets.items():
                value = np.asarray(value) - np.array([int(self.width/2),int(self.height/2)]) #translate targets to center of image
                trans_coord = np.dot(R,np.append(value,1))+np.array([int(self.width/2),int(self.height/2)])
                targ_pos = np.dot(self.coeff,np.append(trans_coord,1))
                print('{0}\t{1:.01f}\t{2:.01f}'.format(key,trans_coord[0],trans_coord[1]))
                self.move_to(targ_pos[1],targ_pos[0])
                sleep(2)
        finally:
            self.move_to(0,0)
            self.unlock()
            #Ugly way to turn the laser off
            #del self.PWM

'''
==============================Trial=============================================
'''
    def run(thisMouse, expSettings, cageSettings, camera, rewarder, headFixer, stimulator, UDPTrigger=None):
        #run matcher


        #Wait for mouse, when mouse inside (RFID tag) for the first time, make object and take image and let user select brain targets
        # Run stimulation, for now without reward and stuff

    def logfile:


if __name__ == '__main__':
