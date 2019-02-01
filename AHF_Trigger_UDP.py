#! /usr/bin/python
#-*-coding: utf-8 -*-

import socket

from AHF_Trigger import AHF_Trigger

class AHF_Trigger_UDP (AHF_Trigger):
    """
    Sends/receives UDP signals as to another pi to start/stop recording

    AHF_UDPTrig uses the socket module to do the UDP stuff, but it should be part of
    the default install
    """
    UDP_PORT = 5007	# special open port 
    @staticmethod
    def about():
        return 'Sends/receives trigger signals over UDP as to another pi to start/stop recording.'

    @staticmethod
    def config_user_get ():
        IPlist =tuple (input('IP addresses of Pis running secondary cameras:').split (','))
        UDPdict = {'IPlist' : IPlist}
        return UDPdict
    
    def setup (self):
        """Makes a new AHF_UDPtrig object using passed in list of ip addresses.

        stores UDPlist in the new object
        sets hasUDP to false if object creation fails because of network error, else True
        """
        try: 
            self.UDPlist = self.settingsDict.get ('IPlist')
            self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind (('', AHF_Trigger_UDP.UDP_PORT))
            self.hasUDP= True
        except socket.error:
            self.hasUDP = False
            print ('AHF_UDPTrig failed to create a socket.')


    def setdown (self):
        del self.sock
    
    def doTrigger (self, message):
        """
        Sends a UDP message to the stored list of  ip addresses
        """
        try:
            for address in self.UDPlist:
                self.sock.sendto (bytes (message, "utf-8"),(address, AHF_Trigger_UDP.UDP_PORT))
        except socket.error as e:
            print ('AHF_UDPTrig failed to send a message: ' + str (e))


    def getTrigger (self):
        """
        Waits for a UDP message and returns a string contaiing the message
        """
        data, addr=self.sock.recvfrom(1024)
        dataStr = data.decode("utf-8")
        return (addr[0], dataStr)
    
    
    def hardwareTest (self):
        response = input ('Enter L to check local (127.0.0.1) only, or R to send to IP list: ')
        message = 'hello_from_AHF_UDPTrig'
        if response [0] == 'L':
            address = '127.0.0.1'
            self.sock.sendto (bytes (message, "utf-8"),(address, AHF_Trigger_UDP.UDP_PORT))
            print (self.getTrigger ())
        else:
            self.doTrigger (message)
        
        response = input ('Do you want to change Trigger_UDP settings ?')
        if response [0] == 'y' or response [0] == 'Y':
            self.settingsDict = self.config_user_get (self.settingsDict)
