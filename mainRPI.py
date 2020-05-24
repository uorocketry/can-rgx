import logging, logging.handlers
from datetime import datetime
import multiprocessing


from rpi.logging.listener import logging_config
from rpi.logging.listener import LoggingListener
from rpi.sensors.sensorstart import start_sensors
from rpi.network.server import server_listen_forever
from shared.customlogging.handler import CustomQueueHandler

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