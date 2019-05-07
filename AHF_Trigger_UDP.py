#! /usr/bin/python
#-*-coding: utf-8 -*-

import socket

from AHF_Trigger import AHF_Trigger

class AHF_Trigger_UDP (AHF_Trigger):
    """
    Sends/receives UDP signals as to another pi to start/stop recording from some device

    AHF_UDPTrig uses the socket module to do the UDP stuff, but it should be part of
    the default install
    """
    default_UDP_PORT = 5007         # port used for UDP
    default_UDP_LIST = '127.0.0.1'  # list of IP addresses to send to

    @staticmethod
    def about():
        return 'Sends/receives trigger signals over UDP as to another pi to start/stop recording movies.'

    @staticmethod
    def config_user_get (starterDict = {}):
        IPlist = starterDict.get ('IPlist',AHF_Trigger_UDP.default_UDP_LIST)
        response = input ('Enter comma-separated list of IP addresses to trigger, currently {:s}: '.format (IPlist))
        if response != '':
            IPlist =tuple (response.split (','))
        portNum = starterDict.get ('UDPport', AHF_Trigger_UDP.default_UDP_PORT)
        response = input ('Enter port number to use for UDP, currently {:d}: '.format (portNum))
        if response != '':
            portNum = int (response)
        starterDict.update({'IPlist' : IPlist, 'UDPport' : portNum})
        return starterDict

    def setup (self):
        """Makes a new AHF_UDPtrig object using passed in list of ip addresses.

        stores UDPlist in the new object
        sets hasUDP to false if object creation fails because of network error, else True
        """
        hasUDP = True
        try:
            self.UDPlist = self.settingsDict.get ('IPlist')
            self.portNum = self.settingsDict.get ('UDPport')
            self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind (('', self.portNum))
        except socket.error:
            print ('AHF_UDPTrig failed to create a socket.')
            hasUDP = False
        return hasUDP

    def setdown (self):
        del self.sock

    def doTrigger (self, message):
        """
        Sends a UDP message to the stored list of  ip addresses
        """
        try:
            for address in self.UDPlist:
                self.sock.sendto (bytes (message, "utf-8"),(address, self.portNum))
        except socket.error as e:
            print ('AHF_UDPTrig failed to send a message: ' + str (e))


    def getTrigger (self):
        """
        Waits for a UDP message and returns a string containing the message
        """
        data, addr=self.sock.recvfrom(1024)
        dataStr = data.decode("utf-8")
        return (addr[0], dataStr)


    def hardwareTest (self):
        from time import sleep
        response = input ('Enter L to check local (127.0.0.1) only, or R to send to IP list: ')
        message = 'hello_from_AHF_UDPTrig'
        if response [0] == 'L':
            address = '127.0.0.1'
            self.sock.sendto (bytes (message, "utf-8"),(address, self.portNum))
            print (self.getTrigger ())
        else:
            self.doTrigger (message)
        sleep (1.0)
        response = input ('Do you want to change Trigger_UDP settings ?')
        if response [0] == 'y' or response [0] == 'Y':
            self.setdown()
            self.settingsDict = self.config_user_get (self.settingsDict)
            self.setup()
