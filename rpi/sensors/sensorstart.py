import threading
import logging
import time
from multiprocessing import Process

from rpi.sensors.thermometer import ThermoList
from rpi.sensors.pressure import Pressure


def start_sensors():
    sensorList = [ThermoList(), Pressure()]


    logging.getLogger(__name__).info("Starting sensor logging")
    for i in sensorList:
        t = threading.Thread(target=i.logging_loop)
        t.daemon = True
        t.start()
