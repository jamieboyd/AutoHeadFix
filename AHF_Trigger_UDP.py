#! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_Trigger import AHF_Trigger
import socket


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
        LEDdelay = float (input ('Delay in seconds between sending UDP and toggling blue LED.'))
        UDPdict = {'IPlist' : IPlist, 'LEDdelay' : LEDdelay}
        return UDPdict
    
    def __init__ (self, UDPdict):
        """Makes a new AHF_UDPtrig object using passed in list of ip addresses.

        stores UDPlist in the new object
        sets hasUDP to false if object creation fails because of network error, else True
        """
        try: 
            self.UDPlist = UDPdict.get ('IPlist')
            self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind (('', AHF_Trigger_UDP.UDP_PORT))
            hasUDP= True
        except socket.error:
            hasUDP = False
            print ('AHF_UDPTrig failed to create a socket.')


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
    
    
#for testing purposes
if __name__ == '__main__':
    hasUDP = True
    UDPdict = {'IPlist' : ('192.168.0.136',), 'LEDdelay' : 2}
    trigger = AHF_UDPTrig (UDPdict)
   
    if hasUDP == True:
        message = 'hello_from_AHF_UDPTrig'
        trigger.doTrigger (message)
        print (trigger.getTrigger ())
