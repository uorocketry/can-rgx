import threading
from rpi.sensors.ThermoList import ThermoList
import logging
import time
from multiprocessing import Process

def start_sensors():
    sensorList = []

    logging.getLogger(__name__).info("Starting sensor logging")
    for i in sensorList:
        t = threading.Thread(target=i.logging_loop)
        t.daemon = True
        t.start()
