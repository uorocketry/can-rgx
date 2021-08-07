import logging
import re
import threading
import time

from rpi.sensors.sensorlogging import SensorLogging
from rpi.sensors.temp_management import TempManagement
from shared.customlogging.errormanager import ErrorManager

import RPi.GPIO as GPIO

RELAY_PIN = 21

thermometer_names = {'28-00000bc725ef': '1',
                     '28-00000bc743d3': '2',
                     '28-00000bc74b3b': '3',
                     '28-00000bca5780': '4',
                     '30-2afaa097a9ae': '5',
                     '32-6afaa097a9ae': '6',
                     '32-aafaa097a9ae': '7',
                     '32-eafaa092a9ae': '8',
                     '48-02581010d213': '9',
                     '28-00000bc9bc5c': '10',
                     '28-00000bc91c30': '11',
                     '28-3c5301074760': '12',
                     '28-00000bc74760': '13'
                    }


class InvalidTemperatureDataError(Exception):
    pass


class InvalidTemperatureRangeError(Exception):
    def __init__(self, temperature):
        self.temperature = temperature


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

        temp = float(temp) / 1000.0

        # Sanity check for the temperature
        if temp < 15 or temp > 75:
            raise InvalidTemperatureDataError(temp)

        return temp

    def run(self):
        em = ErrorManager(__name__)
        while True:
            time.sleep(1)
            try:
                temperature = self.__read()

                # Log to the laptop and files
                self.sensor_logger.info([time.time() * 1000, self.name, temperature])

                # Store in static variable so the temperature management can access it
                ThermometerList.__update_temperature_data(self.name, temperature)

                # If we had a previous error, resolve it
                em.resolve("Error has been cleared for temperature sensor {}".format(self.name), self.name, False)
            except InvalidTemperatureDataError:
                em.error("Temperature sensor {} is returning invalid data. It may have been disconnected."
                         .format(self.name), self.name)
                ThermometerList.__update_temperature_data(self.name, None)
            except InvalidTemperatureRangeError as e:
                em.error("Temperature sensor {} is returning a temperature of {}. This is outside the valid range, "
                         "so discarding it".format(self.name, e.temperature), self.name)
                ThermometerList.__update_temperature_data(self.name, None)
            except (OSError, IndexError, AttributeError):
                em.error("Error reading from temperature sensor {}. Check if it is connected.".format(self.name),
                         self.name)
                ThermometerList.__update_temperature_data(self.name, None)

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
        :param names: A list of all the sensor names (string) to get the data from
        :return: A map with the sensor name as the key and the temperature as the value. If a sensor doesn't exist,
        None will be the value for that sensor
        """
        data = dict()

        with ThermometerList.thermometer_data_lock:
            for k in names:
                if k in ThermometerList.thermometer_data:
                    data[k] = ThermometerList.thermometer_data[k]
                else:
                    data[k] = None

        return data


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

        # next lines added for testing only relay and sensors:
        # print("Starting Relays. Temperature should start rising.")
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(RELAY_PIN, GPIO.OUT)
        # GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn relay on

        # GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn relay off

        # Temperature Management Thread
        time.sleep(10)  # Give some time to the temperature sensors to start returning data
        tempManage = TempManagement()
        tempManage.start()

        # This thread needs to be kept alive to assure the logger works correctly
        while True:
            time.sleep(10000)  # Better on CPU than 'pass'
