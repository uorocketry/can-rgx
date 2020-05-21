import threading
import logging
import time
from multiprocessing import Process

from rpi.sensors.thermometer import ThermoList
from rpi.sensors.vibration import Vibration

def start_sensors():
    sensorList = [ThermoList(), Vibration()]

    logging.getLogger(__name__).info("Starting sensor logging")
    for i in sensorList:
        t = threading.Thread(target=i.logging_loop)
        t.daemon = True
        t.start()
