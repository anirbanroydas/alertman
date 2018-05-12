import random
import json
from email.mime.text import MIMEText

import aiosmtplib

from alertman.usecases.process_alert import AlertSender
from alertman.log import getCustomLogger


log = getCustomLogger(__name__)


class EmailSender(AlertSender):
    def __init__(self, config, loop):
        self._config = config
        self._loop = loop
    
    async def send(self, email):
        # create a new email connection
        smtp = await self._connect()
        # send email now
        await self._createAndSendEmail(email, smtp)

    async def _connect(self):
        # create a new smtp connection 
        # reason for not using the same connection if becasue
        # sinble connectin email is blocking and cannot send paraller email
        # so better to perform multiple email
        smtp = aiosmtplib.SMTP(
            hostname=self._config['SMTP_HOSTNAME'], port=self._config['SMTP_PORT'],
            loop=self._loop, use_tls=self._config['SMTP_USE_TLS']
        )
        await smtp.connect()
        await smtp.login(self._config['SMTP_USERNAME'], self._config['SMTP_PASSWORD'])
        return smtp

    async def _createAndSendEmail(self, email, smtp):
        message = self._createEmailMessage(email)
        await self._sendEmail(message, smtp)
    
    async def _sendEmail(self, message, smtp):
        try:
            await smtp.send_message(message)
        except Exception as exc:
            raise exc
    
    def _createEmailMessage(self, email):
        message = None
        try:
            bodyAsBytes = self._getEmailBodyBytes(email.body)
            message = MIMEText(bodyAsBytes)
            message['From'] = email.sender
            message['To'] = email.receiver
            message['Subject'] = email.subject
        except Exception as exc:
            log.error("Error while creating MIMIEText: exc: {}".format(exc))
            raise exc
        return message
    
    def _getEmailBodyBytes(self, body):
        try:
            if isinstance(body, str):
                return body
            if isinstance(body, bytes):
                return body.decode('utf-8')
            else:
                return json.dumps(body)
        except Exception as exc:
            log.error("Exception raise while parsing emailmessage body: exc: {}".format(exc))
            raise exc