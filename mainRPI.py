import logging, logging.handlers
from datetime import datetime
import multiprocessing
import copy

from rpi.logging.listener import logging_config
from rpi.logging.listener import LoggingListener
from rpi.sensors.sensorstart import start_sensors
from rpi.network.server import server_listen_forever

class CustomQueueHandler(logging.handlers.QueueHandler):
    def __init__(self, queue):
        super().__init__(queue)

    def prepare(self, record):
        '''
        Folowing is copied from the CPython implementation,
        but a line has been changed to prevent the message from
        being converted to a string.
        '''
        # bpo-35726: make copy of record to avoid affecting other handlers in the chain.
        record = copy.copy(record)
        record.exc_info = None
        record.exc_text = None
        return record

if __name__ == '__main__':
    queue = multiprocessing.Queue(-1) #Central queue for the logs
    logListen = LoggingListener(queue) #Start worker which will actually log everything
    logListen.start()

    #Setup logging for main process and all child processes
    h = CustomQueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.INFO)
    
    start_sensors()

    server_listen_forever()