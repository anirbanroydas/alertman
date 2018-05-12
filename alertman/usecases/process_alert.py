import abc

from alertman.log import getCustomLogger
from alertman.domain.email import createAlertObject


log = getCustomLogger(__name__)


class AlertRequest(object):
    def __init__(self, alertMessage, alertType):
	    self.alertMessage = alertMessage
	    self.alertType = alertType


class AlertProcessor(object): 
    def __init__(self, alertSender, validator):
	    self._alertSender = alertSender
	    self._validator = validator


    async def process(self, alertRequest):
        # step 1:  validate the Transaction Request -> Order, PaymentMethod, PaymentInfo
        isValid = self._validator.validate(alertRequest)
        if not isValid:
            raise Exception("AlertProcessor returned invalid for {{ AlertRequest: \
                object: {} }}".format(alertRequest))
        # step 2: Create new domain Transaction ojbect with fraud status false and transaction status pending
        alert = self._createAlert(alertRequest)
        try:
            await self._sendAlert(alert)
        except Exception as exc:
            raise exc

    #---------------------------------------#
    #           Private Methods             #
    #---------------------------------------#

    async def _sendAlert(self, alert):
        try:
            await self._alertSender.send(alert)
        except Exception as exc:
            log.error("self._alertSender.send raised exception: {{ \
                exc: {} }}".format(exc))
            raise exc

    def _createAlert(self, alertRequest):
        return createAlertObject(
            alertRequest.alertMessage, alertRequest.alertType
        )
            

# Interface
class AlertSender(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    async def send(self):
        pass


# Interface
class Validator(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def validate(self, requestObject):
        pass


class EmailAlertValidator(Validator):
    # implememnting the validate method of the Validator Interface
    def validate(self, transReq):
        # dummy service -> hence -> validating always by default
        # real service should have a specific validity check based on the actual Transaction object
        return True


class SMSAlertValidator(Validator):
    # implememnting the validate method of the Validator Interface
    def validate(self, transReq):
        # dummy service -> hence -> validating always by default
        # real service should have a specific validity check based on the actual Transaction object
        return True

