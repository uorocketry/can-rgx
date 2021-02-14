import logging
import multiprocessing

from rpi.logging.listener import LoggingListener
from rpi.network.server import Server
from rpi.sensors.pressure import Pressure
from rpi.sensors.thermometer import Thermometer
from rpi.sensors.vibration import Vibration
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

    #Next lines starts all of the other processes and monitor them in case they quit  
    #processClassesList = [Server, Vibration, Thermometer, Pressure]
    processClassesList = [Thermometer]
    processes = dict()

    for processClass in processClassesList:
        p = processClass()
        p.start()
        processes[processClass] = p

    while True:
        for processClass, process in processes.items():
            if not process.is_alive():
                root.error('The process for {} exited! Restarting it...'.format(processClass.__name__))
                p = processClass()
                p.start()
                processes[processClass] = p