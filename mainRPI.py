import logging
import multiprocessing
import time

from rpi.logging.listener import LoggingListener
from rpi.sensors.thermometer import Thermometer
from shared.customlogging.errormanager import ErrorManager
from shared.customlogging.handler import CustomQueueHandler

if __name__ == '__main__':
    queue = multiprocessing.Queue(-1)  # Central queue for the logs
    logListen = LoggingListener(queue)  # Start worker which will actually log everything
    logListen.start()

    # Setup logging for main process and all child processes
    h = CustomQueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.INFO)

    # Next lines starts all of the other processes and monitor them in case they quit
    #processClassesList = [Server, Vibration, Thermometer, Pressure]
    processClassesList = [Thermometer]
    processes = dict()

    for processClass in processClassesList:
        p = processClass()
        p.start()
        processes[processClass] = p

    em = ErrorManager(__name__)

    while True:
        time.sleep(5)
        for processClass, process in processes.items():
            if not process.is_alive():
                em.error('The process for {} exited! Trying to restart it...'.format(processClass.__name__),
                         processClass.__name__)
                p = processClass()
                p.start()
                processes[processClass] = p
            else:
                em.resolve('{} started successfully'.format(processClass.__name__), processClass.__name__, False)
