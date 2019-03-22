'''
This Stimulator combines LaserStimulation with LickWitholdSpeaker.

It captures a reference image for each mouse and includes a user interface to select targets on reference images.
The Stimulator directs and pulses a laser to selected targets for optogenetic
stimulation/inhibition.

The laser is pulsed whenever the mouse goes for a set amount of time without licking, 
'''

#AHF-specific moudules

from AHF_Stimulator_LaserStimulation import AHF_Stimulator_LaserStimulation
from PTSimpleGPIO import PTSimpleGPIO, Infinite_train, Train
from random import random
import RPi.GPIO as GPIO

#Laser-stimulator modules
from pynput import keyboard
import numpy as np
import sys
import matplotlib.pyplot as plt
from PTPWM import PTPWM
from array import array
from queue import Queue as queue
from threading import Thread
from multiprocessing import Process, Queue
from time import sleep, time
from random import random
from datetime import datetime
from itertools import combinations,product
import imreg_dft as ird
import warnings

def writeToLogFile(logFP, mouse, event):
    """
    Writes the time and type of each event to a text log file, and also to the shell, things that don't go in report after stimulator is done

    Format of the output string: tag     time_epoch or datetime       event
    The computer-parsable time_epoch is printed to the log file and user-friendly datetime is printed to the shell
    :param logFP: file pointer to the log file
    :param mouseObj: the mouse for which the event pertains,
    :param event: the type of event to be printed, entry, exit, reward, etc.
    returns: nothing
    """
    try:
        outPutStr = '{:013}'.format(mouse.tag)
        logOutPutStr = outPutStr + '\t' + '{:.2f}'.format (time ())  + '\t' + event +  '\t' + datetime.fromtimestamp (int (time())).isoformat (' ')
        printOutPutStr = outPutStr + '\t' + datetime.fromtimestamp (int (time())).isoformat (' ') + '\t' + event
        print (printOutPutStr)
        logFP.write(logOutPutStr + '\n')
        logFP.flush()
    except Exception as e:
        print ("Error writing to log file\n", str (e))
        


    
class AHF_Stimulator_LaserStimulation_LW (AHF_Stimulator_LaserStimulation):
    #### default definitions for stimulator configuration that are not defined in superclass
    lickWitholdTime_def = 1  # how long mouse has to go for without licking before getting rewarded
    laser_lead_def = 0.5     # laser pulse is this may seconds before reward is given
    ##### speaker feedback GPIO definitions #######
    speakerPin_def = 25      # GPIO pin used to drive piezo speaker for negative feedback
    speakerFreq_def = 300    # frequency to drive the speaker
    speakerDuty_def = 0.8    # duty cycle to drive speaker, unbalanced duty cycle gives nasty harmonics
    speakerOffForReward_def = 1.5   #time for consuming reward without getting buzzed at

     
    def __init__ (self, cageSettings, expSettings, rewarder, lickDetector, camera):
        super().__init__(cageSettings, expSettings, rewarder, lickDetector, camera)
        self.setup()

    def setup (self):
        # super() sets up all the laser stuff plus self.headFixTime plus # rewards (not used here)
        super().setup()
        #Lick-withold settings
        self.lickWitholdTime = float (self.configDict.get ('lickWitholdTime', self.lickWitholdTime_def))
        self.laser_lead = float (self.configDict.get ('laser_lead', self.laser_lead_def))
        # setting up speaker for negative feedback for licking
        self.speakerPin=int(self.configDict.get ('speaker_pin', self.speakerPin_def))
        self.speakerFreq=float(self.configDict.get ('speaker_freq', self.speakerFreq_def))
        self.speakerDuty = float(self.configDict.get ('speaker_duty', self.speakerDuty_def))
        self.speakerOffForReward = float(self.configDict.get ('speaker_OffForReward', self.speakerOffForReward_def))
        self.speaker=Infinite_train (PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        #Mouse scores
        self.lickWitholdTimes = []
        self.rewardTimes = []
        self.laserTimes = []



    def logfile (self):
        if self.textfp != None:
            for i in range (0, len (self.rewardTimes)):
                if len (self.laserTimes) ==len (self.rewardTimes):
                    self.textfp.write('{:013}\t{:.2f}\tlaser_pulse:lickwithold={:.2f}\t{:s}\n'.format(self.mouse.tag, self.laserTimes [i] ,self.lickWitholdTimes [i], datetime.fromtimestamp (int (self.laserTimes [i])).isoformat (' ')))
                self.textfp.write('{:013}\t{:.2f}\treward\t{:s}\n'.format(self.mouse.tag, self.rewardTimes [i], datetime.fromtimestamp (int (self.rewardTimes [i])).isoformat (' ')))
            self.textfp.flush()
        
#=================Main functions called from outside===========================
    def run(self):

        self.lickWitholdTimes = []
        self.rewardTimes = []
        self.laserTimes = []
        if not hasattr (self.mouse, 'saved_targ_pos'):
            setattr (self.mouse, 'saved_targ_pos', None)
        if self.expSettings.doHeadFix:
            if not hasattr(self.mouse,'ref_im'):
                print('Take reference image')
                writeToLogFile(self.textfp, self.mouse, 'taking reference image')
                self.get_ref_im()
                return
            elif not hasattr(self.mouse,'targets'):
                print('Select targets')
                writeToLogFile(self.testfp, self.mouse, 'no targets selected')
                #If targets haven't been choosen -> release mouse again
                return

            try:
                # Run this only if headfixed
                self.rewarder.giveReward('task')
                #print('Image registration')
                ref_path = self.cageSettings.dataPath+'sample_im/'+datetime.fromtimestamp (int (time())).isoformat ('-')+'_'+str(self.mouse.tag)+'.jpg'
                self.mouse.timestamp = time()
                self.camera.capture(ref_path)
                targ_pos = self.image_registration()
                writeToLogFile(self.textfp, self.mouse, 'no targets selected')
                self.rewarder.giveReward('task')
                if targ_pos is None and self.mouse.saved_targ_pos is not None:
                    targ_pos = self.mouse.saved_targ_pos
                if targ_pos is not None:
                    self.mouse.saved_targ_pos = targ_pos
                    print('Moving laser to target and capture image to assert correct laser position')
                    self.move_to(np.flipud(targ_pos),topleft=True,join=True) #Move laser to target and wait until target reached
                    self.mouse.laser_spot = np.empty((self.camera.resolution[0], self.camera.resolution[1], 3),dtype=np.uint8)
                    self.pulse(70,self.duty_cycle) #At least 60 ms needed to capture laser spot
                    
                    self.camera.capture(self.mouse.laser_spot,'rgb',use_video_port=True)
                    sleep(0.1)
                self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
                #every time lickWitholdtime passes with no licks, make a buzz then give a reward after buzz_lead time.
                self.lickWitholdTimes = []
                self.rewardTimes = []
                self.laserTimes = []
                endTime = time() + self.headFixTime
                speakerIsOn = False
                OffForRewardEnd = 0.0
                while time() < endTime:
                    # setup to start a trial, witholding licking for lickWitholdRandom secs till buzzer
                    lickWitholdRandom = self.lickWitholdTime + (0.5 - random())
                    lickWitholdEnd = time() + lickWitholdRandom
                    # inner loop keeps resetting lickWitholdEnd time until  a succsful withhold
                    while time() < lickWitholdEnd and time() < endTime:
                        anyLicks = self.lickDetector.waitForLick_Soft (0.05)
                        if anyLicks == 0:
                            if speakerIsOn == True:
                                self.speaker.stop_train()
                                speakerIsOn = False
                        else: # there were licks in witholding period
                            if (speakerIsOn == False) and (time() > OffForRewardEnd):
                                self.speaker.start_train()
                                speakerIsOn = True
                            lickWitholdRandom = self.lickWitholdTime + (0.5 - random())
                            lickWitholdEnd = time() + lickWitholdRandom
                    # inner while loop only exits if trial time is up or lick witholding time passed with no licking
                    if anyLicks > 0:
                        break
                    # at this point, mouse has just witheld licking for lickWitholdTime
                    self.lickWitholdTimes.append (lickWitholdRandom)
                    # Give a laser pulse
                    if targ_pos is not None:
                        self.laserTimes.append (time())
                        self.pulse(self.laser_on_time,self.duty_cycle)
                        print ('{:013}\t{:s}\tlaser_pulse:lickwithold={:.2f}'.format(self.mouse.tag, datetime.fromtimestamp (int (time())).isoformat (' '),lickWitholdRandom))
                    # sleep for laser lead time, then give reward
                    sleep (self.laser_lead)
                    self.rewardTimes.append (time())
                    self.rewarder.giveReward('task')
                    print ('{:013}\t{:s}\treward'.format(self.mouse.tag, datetime.fromtimestamp (int (time())).isoformat (' ')))

                    OffForRewardEnd = time() + self.speakerOffForReward
                # make sure to turn off buzzer at end of loop when we exit
                if speakerIsOn == True:
                    self.speaker.stop_train()
                self.mouse.headFixRewards += len (self.rewardTimes)

                """
                # Repeatedly give a reward and pulse simultaneously
                timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
                self.rewardTimes = []
                self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
                for reward in range(self.nRewards):
                    self.rewardTimes.append (time())
                    if targ_pos is not None:
                        self.pulse(self.laser_on_time,self.duty_cycle)
                        writeToLogFile(self.expSettings.logFP, self.mouse, 'laser pulse')
                    self.rewarder.giveReward('task')
                    sleep(timeInterval)
                self.mouse.headFixRewards += self.nRewards
                self.camera.stop_preview()
                """
            finally:
                #Move laser back to zero position at the end of the trial
                self.move_to(np.array([0,0]),topleft=True,join=False)
        else:
            timeInterval = self.rewardInterval - self.rewarder.rewardDict.get ('task')
            self.rewardTimes = []
            self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
            for reward in range(self.nRewards):
                self.rewardTimes.append (time())
                self.rewarder.giveReward('task')
                sleep(timeInterval)
            self.mouse.headFixRewards += self.nRewards
        self.camera.stop_preview()

    def inspect_mice(self,mice,cageSettings,expSettings):
        #Inspect the mice array
        print('MouseID\t\tref-im\ttargets\theadFixStyle\tstimType\tgenotype')
        for mouse in mice.mouseArray:
            ref_im='no'
            targets='no'
            headFixStyle = 'fix'
            if hasattr(mouse,'ref_im'):
                ref_im='yes'
            if hasattr(mouse,'targets'):
                targets='yes'
            if mouse.headFixStyle == 1:
                headFixStyle = 'loose'
            elif mouse.headFixStyle == 2:
                headFixStyle = 'nofix'
            if hasattr(mouse, 'genotype'):
                genotype = expSettings.genotype[mouse.genotype]
            else:
                genotype = 'no genotype'
            stimType = expSettings.stimulator[mouse.stimType][15:22]
            print(str(mouse.tag) + '\t' + str(ref_im) + '\t' + str(targets) +'\t' + headFixStyle + '\t\t' + stimType + '\t\t' + genotype)
        while(True):
            inputStr = input ('c= headFixStyle, t= select targets, s= stimType, g = genotype, q= quit: ')
            if inputStr == 'c':
                while(True):
                    try:
                        inputStr =  int(input ('Type the tagID of mouse to change headFixStyle:'))
                    except ValueError:
                        print("Input is not a valid mouse-id.")
                        break
                    for mouse in mice.mouseArray:
                        if mouse.tag == inputStr:
                            try:
                                inputStr = int(input('Change headFixStyle to:\n0: fix\n1: loose\n2: nofix\n'))
                            except ValueError:
                                print('Input is not a valid number.')
                            if inputStr == 0:
                                mouse.headFixStyle = 0
                            elif inputStr == 1:
                                mouse.headFixStyle = 1
                            elif inputStr == 2:
                                mouse.headFixStyle = 2

                    inputStr = input('Change value of another mouse?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        continue
                    else:
                        break
            elif inputStr == 'g':
                while(True):
                    try:
                        inputStr =  int(input ('Type the tagID of mouse to change genotype:'))
                    except ValueError:
                        print("Input is not a valid mouse-id.")
                        break
                    for mouse in mice.mouseArray:
                        if mouse.tag == inputStr:
                            print('Following genotypes have been specified:')
                            for i,j in enumerate(expSettings.genotype):
                                print(str(i)+': '+j[:])
                            inputStr = int(input('Set genotype to:'))
                            mouse.genotype = inputStr
                    inputStr = input('Change value of another mouse?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        continue
                    else:
                        break
            elif inputStr == 's':
                while(True):
                    try:
                        inputStr =  int(input ('Type the tagID of mouse to change stimType:'))
                    except ValueError:
                        print("Input is not a valid mouse-id.")
                        break
                    for mouse in mice.mouseArray:
                        if mouse.tag == inputStr:
                            print('Following stimTypes are available:')
                            for i,j in enumerate(expSettings.stimulator):
                                print(str(i)+': '+j[15:])
                            inputStr = int(input('Change stimType to:'))
                            mouse.stimType = inputStr

                    inputStr = input('Change value of another mouse?')
                    if inputStr[0] == 'y' or inputStr[0] == "Y":
                        continue
                    else:
                        break
            elif inputStr == 't':
                self.select_targets(mice)
            elif inputStr == 'q':
                break

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
                            alpha=100,
                            fullscreen=False,
                            window = self.camera.AHFpreview)

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
            timeout = 8
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
            self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))

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

        #Average the coefficient matrix obatained by solving all combinations of triplets.
        if len(list(set([x[0] for x in self.laser_points])))>=3:
            self.coeff = []
            for i in combinations(enumerate(zip(self.image_points,self.laser_points)),3):
                ip = np.vstack((i[0][1][0],i[1][1][0],i[2][1][0]))
                lp = np.array([i[0][1][1],i[1][1][1],i[2][1][1]])
                self.coeff.append(solver(ip, lp))
            self.coeff = np.mean(np.asarray(self.coeff),axis=0)

    def get_ref_im(self):
        #Save a reference image whithin the mouse object
        self.mouse.ref_im = np.empty((self.camera.resolution[0], self.camera.resolution[1], 3),dtype=np.uint8)
        self.mouse.timestamp = time()
        self.camera.capture(self.mouse.ref_im,'rgb')

    def select_targets(self,mice):
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
            for mouse in mice.mouseArray:
                if hasattr(mouse,'targets'):
                    inputStr = input('Certain/All mice already have brain targets.\n0: Select targets for remaining mice\n1: Select targets for all registered mice.\n')
                    break
                else:
                    inputStr = str(1)
            if inputStr == str(0):
                for mouse in mice.mouseArray:
                    if (not hasattr(mouse,'targets') and hasattr(mouse,'ref_im')):
                        #print('Mouse: ',mouse.tag)
                        targets_coords = manual_annot(mouse.ref_im)
                        mouse.targets=np.asarray(targets_coords).astype(int)
                        #print('TARGET\tx\ty')
                        #print('{0}\t{1}\t{2}'.format('0',mouse.targets[0],mouse.targets[1]))
                        writeToLogFile(self.textfp, self.mouse, 'Target:x={1},y={2}'.format(mouse.targets[0],mouse.targets[1]))

                        
            if inputStr == str(1):
                for mouse in mice.mouseArray:
                    if hasattr(mouse,'ref_im'):
                        #print('Mouse: ',mouse.tag)
                        targets_coords = manual_annot(mouse.ref_im)
                        mouse.targets=np.asarray(targets_coords).astype(int)
                        #print('TARGET\tx\ty')
                        #print('{0}\t{1}\t{2}'.format('0',mouse.targets[0],mouse.targets[1]))
                        writeToLogFile(self.textfp, self.mouse, 'Target:x={1},y={2}'.format(mouse.targets[0],mouse.targets[1]))

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

        self.mouse.trial_image = np.empty((self.camera.resolution[0], self.camera.resolution[1], 3),dtype=np.uint8)
        self.camera.capture(self.mouse.trial_image,'rgb')

        #Image registration
        #IMPROVE: Could run the registration on a different processor
        warnings.filterwarnings("ignore",".*the returned array has changed*")
        tf = ird.similarity(self.mouse.ref_im[:,:,1],self.mouse.trial_image[:,:,1],numiter=3)
        print('scale\tangle\tty\ttx')
        print('{0:.3}\t{1:.3}\t{2:.3}\t{3:.3}'.format(tf['scale'],tf['angle'],tf['tvec'][0],tf['tvec'][1]))
        #Check if results of image registration don't cross boundaries
        if all((abs(tf['angle'])<=self.max_angle,all(np.abs(tf['tvec'])<=self.max_trans),self.max_scale[0]<=tf['scale']<=self.max_scale[1])):
            #Transform the target to new position
            self.R = trans_mat(tf['angle'],tf['tvec'][1],tf['tvec'][0],tf['scale'])
            cent_targ = self.mouse.targets - np.array([int(self.camera.resolution[0]/2),int(self.camera.resolution[0]/2)]) #translate targets to center of image
            trans_coord = np.dot(self.R,np.append(cent_targ,1))+np.array([int(self.camera.resolution[0]/2),int(self.camera.resolution[0]/2)])
            targ_pos = np.dot(self.coeff,np.append(trans_coord,1))
            #print('TARGET\ttx\tty')
            #print('{0}\t{1:.01f}\t{2:.01f}'.format('0',trans_coord[0],trans_coord[1]))
            writeToLogFile(self.textfp, self.mouse, 'Target Registration:x={1},y={2}'.format(trans_coord[0],trans_coord[1]))
            return targ_pos
        else:
            print('No laser stimulation: Image registration failed.')
            writeToLogFile(self.textfp, self.mouse, 'Target Registration:FAILED')
            return None



    def tester(self,expSettings):
        #Tester function called from the hardwareTester. Includes Stimulator
        #specific hardware tester.
        while(True):
            inputStr = input ('m= matching, v = vib. motor, p= laser tester, c= motor check, a= camera/LED, s= speaker, q= quit: ')
            if inputStr == 'm':
                self.matcher()
                expSettings.stimDict.update({'coeff_matrix' : self.coeff.tolist()})
                expSettings.save()
            elif inputStr == 'p':
                self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
                self.pulse(1000,self.duty_cycle)
                input ('adjust Laser: Press any key to quit ')
                self.camera.stop_preview()
                self.pulse(0)
            elif inputStr == 'a':
                #Display preview and turn on LED
                self.camera.start_preview(fullscreen = False, window = tuple(self.camera.AHFpreview))
                GPIO.output(self.cageSettings.ledPin, GPIO.HIGH)
                GPIO.output(self.cageSettings.led2Pin, GPIO.HIGH)
                input ('adjust camera/LED: Press any key to quit ')
                self.camera.stop_preview()
                GPIO.output(self.cageSettings.ledPin, GPIO.LOW)
                GPIO.output(self.cageSettings.led2Pin, GPIO.LOW)
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

    def h5updater (self,mouse,h5):
        if hasattr(mouse,'ref_im'):
            ref = h5.require_dataset('ref_im',shape=tuple(self.expSettings.camParamsDict['resolution']+[3]),dtype=np.uint8,data=mouse.ref_im)
            ref.attrs.modify('CLASS', np.string_('IMAGE'))
            ref.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
            ref.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
            ref.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
            ref.attrs.modify('IMAGE_MINMAXRANGE', [0,255])
            ref.attrs.modify('timestamp', mouse.timestamp)
        if hasattr(mouse,'targets'):
            h5.require_dataset('targets',shape=(2,),dtype=np.uint8,data=mouse.targets,)
        t = h5.require_group('trial_image')
        if hasattr(mouse,'trial_image'):
            tr = t.require_dataset('trial_'+str(mouse.tot_headFixes),shape=tuple(self.expSettings.camParamsDict['resolution']+[3]),dtype=np.uint8,data=mouse.trial_image)
            tr.attrs.modify('CLASS', np.string_('IMAGE'))
            tr.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
            tr.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
            tr.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
            tr.attrs.modify('IMAGE_MINMAXRANGE', [0,255])
            tr.attrs.modify('timestamp', mouse.timestamp)
        if hasattr(mouse,'laser_spot'):
            ls = t.require_dataset('trial_'+str(mouse.tot_headFixes)+'_laser_spot',shape=tuple(self.expSettings.camParamsDict['resolution']+[3]),dtype=np.uint8,data=mouse.laser_spot)
            ls.attrs.modify('CLASS', np.string_('IMAGE'))
            ls.attrs.modify('IMAGE_VERSION', np.string_('1.2'))
            ls.attrs.modify('IMAGE_SUBCLASS', np.string_('IMAGE_TRUECOLOR'))
            ls.attrs.modify('INTERLACE_MODE', np.string_('INTERLACE_PIXEL'))
            ls.attrs.modify('IMAGE_MINMAXRANGE', [0,255])
            ls.attrs.modify('timestamp', mouse.timestamp)
