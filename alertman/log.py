# Initate logging loggers, and handlers
import logging
from os import getenv


loglevel = getenv('LOG_LEVEL', 'info')
logging.info("logger setup: loglevel: {}".format(loglevel))

LOG_LEVEL = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'error': logging.ERROR
}


def getCustomLogger(loggerName, logLevel=LOG_LEVEL[loglevel]):
    # initiate a logger
    logger = logging.getLogger(loggerName)
    if len(logger.handlers) != 0:
        return logger
    # create formatter
    DEFAULT_FORMAT = '[%(levelname)s]: [%(asctime)s]  [%(name)s] [%(funcName)s:%(lineno)d] - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S %z'
    formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logLevel)
    # add formatter to handler
    handler.setFormatter(formatter)
    # set level for Logger
    logger.setLevel(logLevel)
    # add handler to logger
    logger.addHandler(handler)

    return logger
