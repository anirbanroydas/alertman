import random
from asyncio import sleep

from alertman.usecases.process_alert import AlertSender
from alertman.log import getCustomLogger


log = getCustomLogger(__name__)

    
class SMSSender(AlertSender):
    def __init__(self, config):
        self._config = config
    
    async def send(self, sms):
        # mimic sending email
        log.info("Sending Sms {{ from: {}, to: {} }}".format(
            sms.sender, sms.receiver))
        # sleep randomly for 1-2 sec to mimic actual sms sending
        await sleep(random.uniform(1, 2))
        
        log.info("Sms sent successfully")
