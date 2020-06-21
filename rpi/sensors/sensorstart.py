import logging
import time
import multiprocessing

from rpi.sensors.thermometer import ThermoList
from rpi.sensors.pressure import Pressure
from rpi.sensors.vibration import Vibration

def start_sensors():
    sensorList = [ThermoList(), Pressure(), Vibration()]

    logging.getLogger(__name__).info("Starting sensor logging")
    for i in sensorList:
        i.start()
