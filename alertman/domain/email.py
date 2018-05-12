import time

from alertman.domain.sms import SMSMessage


class EmailMessage(object):
    def __init__(self, sender, receiver, subject='Email Subject', body=''):
        self.emailID = int(time.time()*1000)
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.body = body
    
    def __repr__(self):
        return '{{ EmailMessage: {{ from: {0}, to: {1}, subject: {2} }} }}'.format(
            self.sender, self.receiver, self.subject)
    

def createAlertObject(alertMsg, alertType):
    if alertType == 'email':
        return EmailMessage(alertMsg['sender'], alertMsg['receiver'],
            alertMsg['subject'], alertMsg['body']
        )

    elif alertType == 'sms':
        return SMSMessage(alertMsg['sender'], 
            alertMsg['receiver'], alertMsg['body']
        )
    else:
        raise Exception("Alerttype: {} not available".format(alertType))
    

