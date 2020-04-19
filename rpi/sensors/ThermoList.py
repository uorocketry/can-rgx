from rpi.sensors.Thermo_1wire import Thermo
from rpi.sensors.Sensor import SensorLogging
import glob
import os

import logging
import threading
from rpi.sensors.Thermo_1wire import Thermo


class ThermoList(SensorLogging):
    def __init__(self):
        super().__init__("thermometer", ["id", "value"])
        
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')
    
        self.sensor_list = list()
        
        self.logger = logging.getLogger(__name__)

        for i in device_folders:
            t = Thermo(os.path.basename(i), self.sensorlogger)
            self.sensor_list.append(t)
            self.logger.debug("Found thermometer {} with name {}".format(i, t.name))

        if len(Thermo.names) != len(self.sensor_list):
            self.logger.warning("Not all known thermometers have been found")

    def logging_loop(self):
        for i in self.sensor_list:
            self.logger.debug("Starting {}".format(i.name))
            t = threading.Thread(target = i.logging_loop)
            t.daemon = True
            t.start()