import requests
from time import sleep
class AHF_Notifier:
    """
    Sends a text message using a web service, textbelt.com
    You need to get an account and pay for some messages to get an account key
    
    AHF_Notifier needs requests module, which is not installed by default.
    The best way to install python modules is with pip. Assuming you are using Python 3:
    sudo apt-get install python3-pip
    sudo pip-3 install requests
    """

    @staticmethod
    def config_user_get():
        phoneList =tuple (input('Phone numbers to receive a text message if mouse is in chamber too long:').split(','))
        textBeltKey = input ('Enter the textBelt code (c\'mon it\'s only 65 characters):')
        NotifierDict = {'phoneList': phoneList, 'textBeltKey' : textBeltKey}
        return NotifierDict

    def __init__ (self, NotifierDict):
        """Makes a new AHF_Notifier object
        
        The notifier will send text messages to a tuple of phone numbers using a web service, textbelt.com
        As it uses http requests to send the message to the web service, you need to be online
        for notifier to work.
        :param cageID_p: identifier for cage, sent in message
        :param durationSecs_p: duration that mouse has been in tube, sent in message
        :param phoneList_p: tuple of telephone numbers to which the message will be sent
        :param textBeltKey_p: the account key for the textbelt text messaging service 
        return: nothing
        """
        self.URL = 'http://textbelt.com/text'
        self.cageID = str (NotifierDict.cageID)
        self.phoneList = NotifierDict.phoneList
        self.textBeltKey = NotifierDict.textBeltKey
        self.NotifierDict = NotifierDict

    def notify (self, tag, durationSecs, isStuck):
        """
        Sends a text message with the given information.

        Two types of message can be sent, depending if isStuck is True or False
        No timing is done by the AHF_Notifier class, the durations are only for building the text mssg
        :param tag: RFID tag of the mouse
        :param durationSecs: how long the mouse has been inside the chamber
        :param isStuck: boolean signifying if the mouse has been inside the chamber for too long, or has just left the chamber
        :return: nothing
        """

        if isStuck == True:
            alertString = 'Mouse ' + str(tag) + ' has been inside the chamber of cage ' + self.cageID + ' for {:.2f}'.format(durationSecs/60) + ' minutes.'
        else:
            alertString = 'Mouse ' + str (tag) + ', the erstwhile stuck mouse in cage ' + self.cageID + ' has finally left the chamber after being inside for {:.2f}'.format (durationSecs/60) + ' minutes.'
        for i in self.phoneList:
            requests.post(self.URL, data={'number': i, 'message': alertString, 'key': self.textBeltKey,})
            sleep (2) 
        print (alertString, ' Messages have been sent.')


if __name__ == '__main__':
    import requests
    notifier=AHF_Notifier(18, (17789535102, 16043512437,16047904623), 'c67968bac99c6c6a5ab4d0007efa6b876b54e228IoOQ7gTnT6hAJDRKPnt6Cwc9b')
    notifier.notify (44, 60, 0)

    
