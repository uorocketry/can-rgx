import logging
import threading
import time

from rpi.sensors.sensorlogging import SensorLogging
from rpi.sensors.temp_management import TempManagement

thermometer_names = {'00000bc743d3': '1',
                     '00000bcada29': '2'}


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

    # the read method called from the main class.
    def __read(self):
        lines = self.__read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            lines = self.__read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

    def run(self):
        in_error_state = False
        logger = logging.getLogger(__name__)
        while True:
            try:
                temperature = self.__read()

                # Log to the laptop and files
                self.sensor_logger.info([time.time() * 1000, self.name, temperature])

                # Store in static variable so the temperature management can access it
                ThermometerList.__update_temperature_data(self.name, temperature)

                if in_error_state:
                    in_error_state = False
                    logger.warning("Error has been cleared for {}".format(self.name))
            except OSError:
                if not in_error_state:
                    logger.exception("Error while reading from {}".format(self.name))
                    in_error_state = True

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
        threading.Thread(target=TempManagement.setup).run()
