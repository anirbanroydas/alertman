import abc
import json
from functools import wraps

import aio_pika

from alertman.log import getCustomLogger


log = getCustomLogger(__name__)


class RabbitMQClient(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    async def publish(self, msgToPublish, exchange, routing_key, options=None):
        pass
    
    @abc.abstractmethod
    async def consume(self, queue, exchange, options=None):
        pass


class AioPikaClient(RabbitMQClient):
    
    def __init__(self, username='guest', password='guest',
            host='localhost', port=5672, virtualhoat='/', loop=None):
        self._username = username
        self._password = password
        self._host = host
        self._port = port
        self._virtualhoat = virtualhoat
        self._loop = loop
        self._connection = None
        self._channel = None
        self._exchanges = {}
        self._exchange_types = {
            'direct': aio_pika.ExchangeType.DIRECT,
            'topic': aio_pika.ExchangeType.TOPIC,
            'fanout': aio_pika.ExchangeType.FANOUT
        }
        self._queues = {}
        self._setupDone = False
        self._url = 'amqp://{}:{}@{}:{}{}'.format(
            self._username, self._password, self._host,
            self._port, self._virtualhoat)

    async def publish(self, msgToPublish, exchange='default_exchange',
            routing_key='', options=None):

        if not self._setupDone:
            await self._setUpClient(exchange, options)
        # Sending the message
        currentExchange = None
        try:
            message = self._formatMessage(msgToPublish, options)
            exchangegroup = self._exchanges[exchange]
            currentExchange = exchangegroup['exchange']
            
            await currentExchange.publish(
                message, routing_key=routing_key
            )
        except Exception as exc:
            log.error("AioPikaClient's {}.publish raised exception for: \
                {{ mstToPublish: {}, routine_key: {}, exc: {} }}".format(
                    currentExchange, msgToPublish, routing_key, exc
                )
            )
            raise exc
    
    async def consume(self, queue, exchange, on_message, options=None):
        if not self._setupDone:
            await self._setUpClient(exchange, options)

        if 'set_qos' in options:
            await self._channel.set_qos(prefetch_count=options['set_qos'])

        if queue not in self._queues:
            await self._createAndBindQueue(queue, exchange, options)

        noAck = options.get('noAck', False)
        log.info("[X] Cosuming ... Waiting to get messages ...")
        await self._queues[queue]['queue'].consume(on_message, no_ack=noAck)

    async def setup(self):
        if not self._channel:
            await self._getChannel()
        return self._connection
   
    async def close(self):
        await self._connection.close()
        log.info("AioPikaClient connection closed")

    @property
    def connection(self):
        return self._connection
    
    #---------------------------------------#
    #           Private Methods             #
    #---------------------------------------#

    async def _setUpClient(self, exchange, options):
        if not self._channel:
            await self._getChannel()
        
        if exchange not in self._exchanges:
            await self._getExchange(exchange, options)
        
        self._setupDone = True
   
    async def _getConnection(self):
        try:
            self._connection = await aio_pika.connect_robust(self._url)
        except Exception as exc:
            log.error("AioPikaClient's aio_pika.connect_robust raised\
                exception for: {{ self._url: {}, exc: {} }}".format(self._url, exc))
            raise exc
        
        log.info("AioPikaClient connection established")
        return self._connection

    async def _getChannel(self):
        if not self._connection:
            await self._getConnection()
        if not self._channel:
            try:
                self._channel = await self._connection.channel()
            except Exception as exc:
                log.error("AioPikaClient's self._connection.channel()\
                    raised exception: {}".format(exc))
                raise exc
                
            log.info("AioPikaClient channel established")
        return self._channel

    async def _getExchange(self, exchange, options):
        # create a new exhange and bind to routing_key
        exchangeType = None
        if 'exchangeType' in options:
            exchangeType = self._exchange_types[options['exchangeType']]
        
        currentExchange = self._channel.default_exchange
        if exchangeType:
            try:
                currentExchange = await self._channel.declare_exchange(
                    exchange, exchangeType
                )
            except Exception as exc:
                log.error("AioPikaClient's self._channel.declare_exchange \
                    raised exception for: {{ exchange: {}, exhangeType: {},\
                    exc: {} }}".format(exchange, exchangeType, exc))
                raise exc
        
        self._exchanges[exchange] = {
            'exchange': currentExchange,
            'type': exchangeType
        }
        return currentExchange
   
    async def _createAndBindQueue(self, queue, exchange, options):
        currentQueue = await self._createQueue(queue, options)

        bindingKeys = await self._bindQueue(currentQueue, exchange, options)
        
        self._queues[queue] = {
            'queue': currentQueue,
            'bindingKeys': bindingKeys
        }
        return currentQueue

    async def _createQueue(self, queue, options):
        durable = options.get('queueDurable', False)
        try:
            currentQueue = await self._channel.declare_queue(
                queue, durable=durable
            )
        except Exception as exc:
            log.error("AioPikaClient's self._channel.declare_queue \
                raised exception for: {{ queue: {}, durable: {}, \
                exc: {} }}".format(queue, durable, exc))
            raise exc

        return currentQueue
   
    async def _bindQueue(self, queue, exchange, options):
        bindingKeys = options.get('bindingKey', None)
        if not bindingKeys and self._exchanges[exchange]['type'] in (
                    self._exchange_types.keys()
                ):
            raise Exception("Binding Key required for the specified exchange")
        
        if bindingKeys:
            if isinstance(bindingKeys, str):
                bindingKeys = [bindingKeys]
            for binding_key in bindingKeys:
                try:
                    await queue.bind(
                        self._exchanges[exchange]['exchange'], routing_key=binding_key
                    )
                except Exception as exc:
                    log.error("AioPikaClient's queue.bind raised exception for: \
                        {{ queue: {}, exchange: {}, routine_key: {}, \
                        exc: {} }}".format(
                            queue, self._exchanges[exchange]['exchange'],
                            binding_key, exc
                        )
                    )
                    raise exc

        return bindingKeys

    def _formatMessage(self, msgToPublish, options):
        data = {
            'message': msgToPublish
        }
        message = data
        try:
            message = json.dumps(data).encode()
        except Exception as exc:
            log.error("AioPikaClient's json.dumps raised exception for: \
                {{ data: {}, exc: {} }}".format(data, exc))

        delivery = options.get('deliverMode', None)
        deliveryMode = aio_pika.DeliveryMode.NOT_PERSISTENT
        if delivery == 'persistent':
           deliveryMode = aio_pika.DeliveryMode.PERSISTENT
        try:
            formattedMessage = aio_pika.Message(
                message, delivery_mode=deliveryMode
            )
            return formattedMessage
        except Exception as exc:
            log.error("AioPikaClient's aio_pika.Message raised exception \
                for: {{ message: {}, delivery_mode: {}, exc: {} }}".format(
                    message, deliveryMode, exc
                )
            )
            raise exc
