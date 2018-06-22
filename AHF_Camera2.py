#! /usr/bin/python3
#-*-coding: utf-8 -*-

from AutoHeadFix.AHF_Camera import AHF_Camera
import os
import socket
import json
import pwd
import grp



def Camera2Run ():
    """
    AHF_Camera2 is a stand-alone program running on a dedicated Rpi that controls a secondary camera trigered by a UDP command from the Rpi running the main task

    AHF_Camera2Run waits for a UDP start signal containing some metadata, which it incorporates into a filename for the video it records,
    stopping the video upon receipt of a UDP signal whose message is "Stop"
    There may be more than 1 secondary camera, recording different aspects of mouse behaviour during the task.

    The AHF_Camera class from AutoHeadFix is used to control the PiCamera

    Camera2 saves settings in a JSON dictionary file, ./Camera2_settings.jsn, for the following information:
    dataPath          The file path to the folder where the recorded video will be stored
    UDP_SENDER        IP address of the Rpi running the main task, which sends the start and stop signals
    UDP_IP            IP address of the interface to look at on this computer, or just leave blank and it will look on all interfaces
    UDP_PORT          use any one of the many non-assigned port numbers
    maxRecSecs        The maximum number of seconds to record video after getting a start signal, a fail-safe if connection is lost after starting

    plus the settings for the AHF_camera used.
    """
    try:
        with open ('./Camera2_settings.jsn', 'r') as fp:
            configDict = json.loads(fp.read())
            fp.close()
    except IOError:
        #we will make default settings if we didn't find file
        print ('Unable to open Camera2_settings.jsn, using default settings, please edit new settings.')
        configDict = {'dataPath' : '/home/pi/Documents/', 'UDP_Sender' : '127.0.0.1', 'UDP_IP' : '', 'UDP_Port' : 2211, 'maxRecSecs' : 30.0}
    try:
        camera2 = AHF_Camera (configDict)  
    except Exception as anError:
        print ("Quitting, Camera not initialized.." + str (anError))
        return    
    event = input ('enter \'e\' to edit settings, or any other character to start waiting for UDP events\n:')
    if event == 'e' or event == "E":
       editConfig(configDict, camera2)
    
    try:
        sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	# set up UDP port for listening
        sock.bind ((configDict.get('UDP_IP'), configDict.get ('UDP_Port')))
    except socket.error:
        print ("Quitting, Could not make a socket connection.")
        return
    isCapturing=False
    while True:
        if isCapturing == True:
            sock.settimeout (configDict.get ('maxRecSecs'))
            print ('Waiting for a Stop Trigger.')
        else:
             print ('Waiting for a Start Trigger.')
             sock.settimeout (None)
        try:
            data, addr=sock.recvfrom(1024)
            dataStr = data.decode("utf-8")
            addStr = addr[0]
            if addStr == configDict.get ('UDP_Sender'):
                if ((isCapturing == False) and (dataStr != 'Stop')):
                    camera2.start_recording (configDict.get ('dataPath') + dataStr  +  '.' + camera2.AHFvideoFormat)
                    isCapturing = True
                    print ('Capturing "' + dataStr + '"...', end=' ')
                elif ((isCapturing) and (dataStr == 'Stop')):
                    camera2.stop_recording ()
                    isCapturing = False
                    print ('Ending Capture with Stop...', end=' ')
            else:
                print ('That\'s not my partner sending this message')
        except socket.error as e:
            if (isCapturing == True): #and (e == socket.timeout):
                print ('isCapuring=',isCapturing, 'socket error=', e)
                camera2.stop_recording ()
                isCapturing = False
                print ('Ending Capture with time out..', end = ' ')
            else:
                print ('socket error = ', e)
                



def showConfig (configDict, camera2):
    """
    Shows the settings currently in use for AHF_Camera2. First the camera settings, then the settings related to UDP and saving data
    
    :param configDict: dictionary containing settings
    :param camera2: the AHF camera in use, so it can print its own config
    """
    camera2.show_config ()
    print ('----------------Camera2 program Settings----------------')
    print ('10:File path to the folder where the recorded video will be stored: ' + configDict.get ('dataPath'))
    print ('11:IP address of the Rpi running the main task, which sends the start and stop signals: ' + configDict.get ('UDP_Sender'))
    print ('12:Port number to use for UDP - any  non-assigned Port number will do: ' + str (configDict.get ('UDP_Port')))
    print ('13:IP address of the interface on this computer used to listen for UDP signals, or \'\' to listen on all interfaces: ' + str(configDict.get ('UDP_IP')))
    print ('14:Maximum number of seconds to record video after getting a start signal, ' + str(configDict.get ('maxRecSecs')))
   


def editConfig(configDict, camera2):
    """
    Allows the User to edit config settings for AHF_Camera2 and to save the configs to a file

    :param configDict: dictionary containing settings
    :param camera2: the AHF camera in use, so it can print and edit its own config
    """
    while True:
        showConfig (configDict, camera2)
        selNum= int (input('Enter a number to adjust settings, or 0 to save the settings and start waiting for events:'))
        if selNum == 0:
            with open ('./Camera2_settings.jsn', 'w') as fp:
                fp.write (json.dumps (configDict))
                fp.close ()
            uid = pwd.getpwnam ('pi').pw_uid
            gid = grp.getgrnam ('pi').gr_gid
            os.chown ('Camera2_settings.jsn', uid, gid)
            break
        if selNum < 10:
            camera2.adjust_config_from_user() # get user to adjust camera settings
            configDict.update (camera2.get_configDict()) # add camera settings to config dict so they can be saved to file
        elif selNum == 10:
            tempInput = input ('Enter file path:')
            configDict.update ({'dataPath' : tempInput})
        elif selNum == 11:
            tempInput = input ('Enter IP address of the Rpi running the main task:')
            configDict.update ({'UDP_Sender' : tempInput})
        elif selNum ==12:
            tempInput = input ('Enter port number to use for UDP:')
            configDict.update ({'UDP_Port' : int (tempInput)})
        elif selNum == 13:
            tempInput = input ('Enter IP address of host interface :')
            configDict.update ({'UDP_IP' : tempInput})
        elif selNum == 14:
            tempInput = input('Enter maximum number of seconds to record video:')
            configDict.update ({'maxRecSecs' : float (tempInput)})


if __name__ == '__main__':
    Camera2Run ()
