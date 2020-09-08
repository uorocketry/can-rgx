import glob
import logging
import os
import threading
import time

from sensorlogging import SensorLogging


"""
THESE OPERATIONS WILL BE DONE IN THE TEMP SENSOR CODE 'thermometer.py'. THIS PROGRAM IS JUST
FOR TESTING.
"""


class Thermo:
    names = {'00000bc743d3': '1',
             '00000bcada29': '2'}

    def __init__(self, identity, sensorlogger):
        self.device_file = '/sys/bus/w1/devices/' + identity + '/w1_slave'
        self.sensorlogger = sensorlogger
        self.logger = logging.getLogger(__name__)

        if identity in Thermo.names:
            self.logger.debug("Thermometer {} has been added".format(identity))
            self.name = Thermo.names[identity]
        else:
            self.logger.warning("Thermometer with identity {} is not listed in known sensors".format(identity))
            self.name = 'UNDEFINED'

    def read_temp_raw(self):
        f = open(self.device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    # the read method called from the main class.
    def read(self):
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

    def logging_loop(self):
        inErrorState = False
        while True:
            try:
                self.sensorlogger.info([time.time() * 1000, self.name, self.read()])

                if inErrorState:
                    inErrorState = False
                    self.logger.warning("Error has been cleared for {}".format(self.name))
            except OSError:
                if not inErrorState:
                    self.logger.exception("Error while reading from {}".format(self.name))
                    inErrorState = True


class ThermoList(SensorLogging):
    def setup(self):
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')

        self.sensor_list = list()

        logger = logging.getLogger(__name__)

        for i in device_folders:
            t = Thermo(os.path.basename(i), self.sensorlogger)
            self.sensor_list.append(t)
            logger.debug("Found thermometer {} with name {}".format(i, t.name))

        if len(Thermo.names) != len(self.sensor_list):
            logger.warning("Not all known thermometers have been found")

    def pass_value(self, sensor_id):
        """
        Method to pass value to temperautre management process
        """
        self.id = sensor_id

        ret_temp_list = []

        for i in self.sensor_list:
            #create list with values of interest that will be returned
            if i == self.id:
               #call self.read() --> returns temp_c --> pass to temp_management
                target_temp = i.read()
                ret_temp_list.append(target_temp)
                return ret_temp_list



    def run(self):
        super().setup_logging("thermometer", ["id", "value"])
        self.setup()
        logger = logging.getLogger(__name__)

        for i in self.sensor_list:
            logger.debug("Starting {}".format(i.name))
            t = threading.Thread(target=i.logging_loop)

            t.daemon = True
            t.start()

        while True:
            pass