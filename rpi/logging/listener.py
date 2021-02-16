import logging
import logging.handlers
import multiprocessing
import sys

import shared.config as config
from rpi.network.bufferedsockethandler import BufferedSocketHandler
from shared.customlogging.filter import SensorFilter
from shared.customlogging.handler import MakeFileHandler


class LoggingListener(multiprocessing.Process):
    """
    Continuously checks the queue and processes any logs inside. Uses logging_config()
    to setup the handling of the logs.
    """

    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def run(self):
        logging_config()
        while True:
            while not self.queue.empty():
                record = self.queue.get()
                logger = logging.getLogger(record.name)
                logger.handle(record)


def logging_config():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    loggingFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    loggingFilter = SensorFilter()

    # Logging to console
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(loggingFormat)
    consoleHandler.addFilter(loggingFilter)
    logger.addHandler(consoleHandler)

    # Logging to file. A new file is created each run, with the name being the current date and time
    fileHandler = MakeFileHandler('rpi', 'main')
    fileHandler.setFormatter(loggingFormat)
    fileHandler.addFilter(loggingFilter)
    logger.addHandler(fileHandler)

    RPIConfig = config.get_config('rpi')
    socketHandler = BufferedSocketHandler(RPIConfig['laptop_ip'], logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    logger.addHandler(socketHandler)
