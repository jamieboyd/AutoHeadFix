import requests
from time import sleep
from AHF_Notifier import AHF_Notifier

class AHF_Notifier_Requests(AHF_Notifier):
    """
    sends text messages to a tuple of phone numbers using a web service, textbelt.com
    You need to get an account and pay for some messages to get an account key
    As it uses http requests to send the message to the web service, your Pi needs to be online

    AHF_Notifier_Requests needs requests module, which is not installed by default.
    The best way to install python modules is with pip. Assuming you are using Python 3:
    sudo apt-get install python3-pip
    sudo pip-3 install requests
    """
    textBeltURL = 'http://textbelt.com/text'

    @staticmethod
    def about():
        return 'Sends a text message using a paid web service, textbelt.com'

    @staticmethod
    def config_user_get(starterDict = {}):
        phoneList = starterDict.get('phoneList',()) # no useful default values for phonelist or textbelt key
        response = input('Enter phone numbers to receive text messages, currently %s :' % str(phoneList))
        if response != '':
            phoneList =tuple(response.split(','))
        textBeltKey = starterDict.get('textBeltKey', '') # no useful default values for phonelist or textbelt key
        response = input('Enter the textBelt code, currently %s: ' % textBeltKey)
        if response != '':
            textBeltKey = response
        starterDict.update({'phoneList': phoneList, 'textBeltKey' : textBeltKey})
        return starterDict

    def setup(self):
        self.phoneList = self.settingsDict.get('phoneList')
        self.textBeltKey = self.settingsDict.get('textBeltKey')

    def setdown(self):
        pass

    def notifyStuck(self, tag, cageID, duration, isStuck):
        """
        Sends a text message with the given information.

        Two types of message can be sent, depending if isStuck is True or False
        No timing is done by the AHF_Notifier class, the durations are only for building the text mssg
        :param tag: RFID tag of the mouse
        :param durationSecs: how long the mouse has been inside the chamber
        :param isStuck: boolean signifying if the mouse has been inside the chamber for too long, or has just left the chamber
        :return: nothing
        """
        if isStuck:
            alertString = 'Mouse {:d}'.format(tag) + ' has been inside the chamber of cage ' + cageID + ' for {:.2f}'.format(durationSecs/60) + ' minutes.'
        else:
            alertString = 'Mouse {:d}'.format(tag) + ', the erstwhile stuck mouse in cage ' + cageID + ' has finally left the chamber after being inside for {:.2f}'.format(durationSecs/60) + ' minutes.'
        for i in self.phoneList:
            requests.post(self.textBeltURL, data={'number': i, 'message': alertString, 'key': self.textBeltKey,})
            sleep(2)
        print(alertString, ' Messages have been sent.')


    def notify(self, msgStr):
        for i in self.phoneList:
            requests.post(self.textBeltURL, data={'number': i, 'message': msgStr, 'key': self.textBeltKey,})
            sleep(2)
        print(msgStr, ' Messages have been sent.')



if __name__ == '__main__':
    import requests
    notifier=AHF_Notifier(18,(17789535102, 16043512437,16047904623), 'c67968bac99c6c6a5ab4d0007efa6b876b54e228IoOQ7gTnT6hAJDRKPnt6Cwc9b')
    notifier.notify(44, 60, 0)
