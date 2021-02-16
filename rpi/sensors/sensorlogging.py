import logging
import multiprocessing
from abc import ABC, abstractmethod

from shared.customlogging.formatter import CSVFormatter
from shared.customlogging.handler import MakeFileHandler


class SensorLogging(ABC, multiprocessing.Process):
    """
    Base class for pretty much all sensors. This class main function is to create the logger for each sensors.
    """

    def setup_logging(self, folderName, dataRow):
        """
        Parameters:
            folderName : name of the folder to use
            dataRow : list representing the header of the csv file. Do not include timestamp, it will be included automatically

        Sets up the sensor logging for the base class, i.e. create a file where all the data specifically for this
        sensor is written to. The logger can be access by the base class at `self.sensorlogger`.

        Side note: Other lower-level loggers (ex: the root logger) can do other things with this data. For example, the
        root logger can be configured to send data over a network connection to somewhere else. This method only assures
        the data is written to a local file.
        """

        self.sensorlogger = logging.getLogger("sensorlog." + folderName)

        csvHandler = MakeFileHandler('rpi', 'sensor', folderName, 'csv')
        csvHandler.setFormatter(CSVFormatter())
        self.sensorlogger.addHandler(csvHandler)
        self.sensorlogger.setLevel(logging.INFO)

        self.sensorlogger.info(["timestamp", *dataRow])

    @abstractmethod
    def run(self):
        pass
