from abc import ABC, abstractmethod
import logging
from datetime import datetime

from shared.customlogging.formatter import CSVFormatter
from shared.customlogging.handler import MakeFileHandler

class SensorLogging(ABC):
    '''
    Base class for pretty much all sensors. This class main function is to create the logger for each sensors.
    '''
    def __init__(self, folderName, dataRow):
        '''
        Parameters:
            folderName : name of the folder to use
            dataRow : list representing the header of the csv file. Do not include timestamp, it will be included automatically
        '''

        self.sensorlogger = logging.getLogger("sensorlog."+folderName)

        csvHandler = MakeFileHandler("logs/sensor/"+folderName+"/"+datetime.now().strftime("{}_%Y-%m-%d %H-%M-%S.csv".format(folderName)))
        csvHandler.setFormatter(CSVFormatter())
        self.sensorlogger.addHandler(csvHandler)
        self.sensorlogger.setLevel(logging.INFO)

        self.sensorlogger.info(["timestamp", *dataRow])

    @abstractmethod
    def logging_loop(self):
        pass