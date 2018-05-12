import asyncio
import os
import json

from alertman.log import getCustomLogger
from rabbitmq_client import AioPikaClient
from alertman.usecases.process_alert import (
    AlertRequest, AlertProcessor,
    EmailAlertValidator, SMSAlertValidator
)
from alertman.usecases.send_email import EmailSender
from alertman.usecases.send_sms import SMSSender


log = getCustomLogger(__name__)
usecases = {}


async def startConsuming(app, on_message_function):
    options = {
        'set_qos': 1,
        'exchangeType': 'topic',
        'queueDurable': True,
        'bindingKey': 'dummy-alerts',
        'deliverMode': 'persistent'
    }

    await app.consume(
        'dummy_alerts_queue', 'dummy-exchange', 
        on_message_function, options
    )
        

async def setupMessageBroker(loop, config):
    client = AioPikaClient(
        username=config['MESSAGE_BROKER_SERVICE_USERNAME'],
        password=config['MESSAGE_BROKER_SERVICE_PASSWORD'],
        host=config['MESSAGE_BROKER_SERVICE_HOST'],
        port=config['MESSAGE_BROKER_SERVICE_PORT'],
        virtualhoat=config['MESSAGE_BROKER_SERVICE_VIRTUALHOST'],
        loop=loop
    )
    # setup the connection and channel that will be used across the app
    log.info("Setting up Message Broker...")
    await client.setup()
    return client


def setupUseCaseDependencies(loop, config):
    global usecases
    emailAlertSender = EmailSender(config, loop)
    emailAlertValidator = EmailAlertValidator()
    
    smsAlertSender = SMSSender(config)
    smsAlertValidator = SMSAlertValidator()

    emailAlertProcessor = AlertProcessor(emailAlertSender, emailAlertValidator)
    smsAlertProcessor = AlertProcessor(smsAlertSender, smsAlertValidator)
    
    usecases['emailAlertProcessor'] = emailAlertProcessor
    usecases['smsAlertProcessor'] = smsAlertProcessor

    # add the email alerting for transction configs
    usecases['emailSender'] = config['TRANSACTION_FRAUD_EMAIL_ALERT_FROM']
    usecases['emailReceiver'] = config['TRANSACTION_FRAUD_EMAIL_ALERT_TO']
    usecases['emailSubject'] = config['TRANSACTION_FRAUD_EMAIL_ALERT_SUBJECT']

    # add alerting configs fro sms transaction fraud
    usecases['smsSender'] = '10101010'
    usecases['smsReceiver'] = '010010101'


async def setupApp(loop, config):
    app = await setupMessageBroker(loop, config)
    setupUseCaseDependencies(loop, config)
    return app


async def startWorker(loop, config):
    # setup the app
    app = await setupApp(loop, config)
    # start consuming via the alerts_consumer
    await startConsuming(app, alerts_consumer)
    

async def alerts_consumer(message):
    try:
        # read raw bytes data from message.body and decode it to unicode
        messageContent = message.body.decode('utf-8')
        # convert str to python dictionary
        messageObj = json.loads(messageContent)
        # the real message is in the field 'message'
        messageContent = messageObj['message']
        # read the alertTypes, eg: ['sms', 'email']
        alertTypes = messageContent['alertTypes']
        # create coroutine tasks(futures) to exectute in asyncrhronously concurrently
        # since there can be multipel alerts required
        tasks = [processAlert(alertType, messageContent) for alertType in alertTypes]
        # wait for the tasks to complete
        await asyncio.wait(tasks)
    
    except Exception as exc:
        log.error("Exception while waiting for tasks: {}".format(exc))
    # snnd consumer message acknowledgement so that the message can be removed
    # from the rabbitmq queueu
    message.ack()


async def processAlert(alertType, alert):
    alertRequest = getAlertRequest(alertType, alert)
    alertProcessor = getAlertProcessor(alertType)
    if alertProcessor:
        await alertProcessor.process(alertRequest)


def getAlertRequest(alertType, alert):
    alertReq = AlertRequest(
        alertMessage=getAlertMessage(alertType, alert),
        alertType=alertType
    )
    return alertReq

def getAlertMessage(alertType, alert):
    sender, receiver, subject = '', '', ''
    if alertType == 'email':
        sender = usecases['emailSender']
        receiver = usecases['emailReceiver']
        subject = usecases['emailSubject']
    elif alertType == 'sms':
        sender = usecases['smsSender']
        receiver = usecases['smsReceiver']
    
    message = {
        'sender': sender,
        'receiver': receiver,
        'subject': subject,
        'body': alert['message']
    }
    return message

def getAlertProcessor(alertType):
    global usecases
    alertProcessor = None
    if alertType == 'email':
        alertProcessor = usecases['emailAlertProcessor']
    elif alertType == 'sms':
        alertProcessor = usecases['smsAlertProcessor']
    else:
        log.error("Alert type: {} does not exist".format(alertType))
    return alertProcessor


def getConfigFromEnvironment():
    config = {
        # rabbitmq realted config to receive alert messages
        'MESSAGE_BROKER_SERVICE_PASSWORD': os.getenv('MESSAGE_BROKER_SERVICE_PASSWORD'),
        'MESSAGE_BROKER_SERVICE_USERNAME': os.getenv('MESSAGE_BROKER_SERVICE_USERNAME'),
        'MESSAGE_BROKER_SERVICE_HOST': os.getenv('MESSAGE_BROKER_SERVICE_HOST'),
        'MESSAGE_BROKER_SERVICE_PORT': int(int(os.getenv('MESSAGE_BROKER_SERVICE_PORT'))),
        'MESSAGE_BROKER_SERVICE_VIRTUALHOST': os.getenv('MESSAGE_BROKER_SERVICE_VIRTUALHOST'),
        
        # smtp related config for sending email
        'SMTP_HOSTNAME': os.getenv('SMTP_HOSTNAME'),
        'SMTP_PORT': int(os.getenv('SMTP_PORT')),
        'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
        'SMTP_USE_TLS': bool(os.getenv('SMTP_USE_TLS')),

        # email transaction fruad alerting configs
        'TRANSACTION_FRAUD_EMAIL_ALERT_FROM': os.getenv('TRANSACTION_FRAUD_EMAIL_ALERT_FROM'),
        'TRANSACTION_FRAUD_EMAIL_ALERT_TO': os.getenv('TRANSACTION_FRAUD_EMAIL_ALERT_TO'),
        'TRANSACTION_FRAUD_EMAIL_ALERT_SUBJECT': os.getenv('TRANSACTION_FRAUD_EMAIL_ALERT_SUBJECT')
    }
    return config
    

if __name__ == "__main__":
    # read config from environment
    config = getConfigFromEnvironment()
    # create a new asynio event loop
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(startWorker(loop, config))
    try:
        loop.run_forever()
    except Exception as exc:
        log.error("Exception occured: {}".format(exc))
        loop.close()


