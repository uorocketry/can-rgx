import logging
import re
import threading
import time

from rpi.sensors.sensorlogging import SensorLogging
from rpi.sensors.temp_management import TempManagement
from shared.customlogging.errormanager import ErrorManager

thermometer_names = {'00000bc743d3': '1',
                     '00000bcada29': '2'}


class InvalidTemperatureDataError(Exception):
    pass


class ThermometerList(threading.Thread):
    """
    Class to retrieve data from temperature sensors

    Each instance of this class represents a separate temperature sensor. Also contains a static variable to keep track
    of the current temperature of all sensors.
    """

    thermometer_data = dict()
    thermometer_data_lock = threading.Lock()

    def __init__(self, identity, name, sensor_logger):
        super().__init__()
        self.device_file = '/sys/bus/w1/devices/' + identity + '/w1_slave'
        self.sensor_logger = sensor_logger
        self.name = name

    def __read_temp_raw(self):
        f = open(self.device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    '''
    Reads and returns the temperature of this sensor
    '''

    def __read(self):
        lines = self.__read_temp_raw()

        # The following regex retrieves the result of the CRC check
        crc = re.match(r'^(?:\w{2} ){9}: crc=\w+ (\w+)$', lines[0]).group(1)
        if crc != 'YES':
            raise InvalidTemperatureDataError  # CRC check failed, so the data is not valid

        # Now, this regex retrieves the actual temperature
        temp = re.match(r'^(?:\w{2} ){9}t=(\d+)$', lines[1]).group(1)

        return float(temp) / 1000.0

    def run(self):
        em = ErrorManager(__name__)
        while True:
            try:
                temperature = self.__read()

                # Log to the laptop and files
                self.sensor_logger.info([time.time() * 1000, self.name, temperature])

                # Store in static variable so the temperature management can access it
                ThermometerList.__update_temperature_data(self.name, temperature)

                # If we had a previous error, resolve it
                em.resolve("Error has been cleared for {}".format(self.name), self.name, False)
            except InvalidTemperatureDataError:
                em.error(
                    "Temperature sensor {} is returning invalid data. It may have been disconnected.".format(self.name),
                    self.name)
            except OSError:
                em.error("Error reading from temperature sensor {}. Check if it is connected.".format(self.name),
                         self.name)

    @staticmethod
    def __update_temperature_data(name, data):
        """
        Update the temperature of the specified sensor
        :param name: The sensor name
        :param data: The temperature data to replace with
        """
        with ThermometerList.thermometer_data_lock:
            ThermometerList.thermometer_data[name] = data

    @staticmethod
    def get_temperature_data(name):
        """
        Return the temperature data of a single sensor
        :param name: The sensor to get the data from
        :return: The temperature if the sensor exists. If it doesn't exists, None is returned.
        """
        return ThermometerList.get_temperature_data_list([name])

    @staticmethod
    def get_temperature_data_list(names):
        """
        Return the temperature data of a list of sensors.
        :param names: A list of all the sensor names to get the data from
        :return: A map with the sensor name as the key and the temperature as the value. If a sensor doesn't exist,
        None will be the value for that sensor
        """
        with ThermometerList.thermometer_data_lock:
            return dict((k, ThermometerList.thermometer_data[k] if k in ThermometerList.thermometer_data else None)
                        for k in names)


class Thermometer(SensorLogging):
    """
    Simply used to start the logging of the temperature sensors and start the temperature management thread.
    This class doesn't contain any other logic.
    """

    def start_thermometer_threads(self):
        logger = logging.getLogger(__name__)

        for identity, name in thermometer_names.items():
            t = ThermometerList(identity, name, self.sensorlogger)
            t.start()
            logger.debug("Started {} thermometer".format(name))

    def run(self):
        super().setup_logging("thermometer", ["id", "value"])

        self.start_thermometer_threads()

        # temp management thread
        threading.Thread(target=TempManagement.setup(self)).run()
