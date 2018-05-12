import abc
import time


class AlertMessage(object):
    def __init__(self, messageBody, messageType):
        self._messageBody = messageBody
        self.messageType = messageType


class SMSMessage(object):
    def __init__(self, sender, receiver, body=''):
        self.smsID = self.emailID = int(time.time()*1000)
        self.sender = sender
        self.receiver = receiver
        self.body = body
    
    def __repr__(self):
        return '{{ SMSMessage: {{ from: {0}, to: {1} }}'.format(
            self.sender, self.receiver)
