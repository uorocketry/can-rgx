import sys
import logging, logging.handlers
from datetime import datetime

from shared.customlogging.handler import MakeFileHandler
from shared.customlogging.filter import SensorFilter
from rpi.sensors.sensorstart import start_sensors
from rpi.network.server import server_listen_forever

#Setting up logging to console and file

logger = logging.getLogger()
logger.setLevel(logging.INFO)

loggingFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
loggingFilter = SensorFilter()

#Logging to console
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(loggingFormat)
consoleHandler.addFilter(loggingFilter)
logger.addHandler(consoleHandler)

#Logging to file. A new file is created each run, with the name being the current date and time
fileHandler = MakeFileHandler('rpi', 'main')
fileHandler.setFormatter(loggingFormat)
fileHandler.addFilter(loggingFilter)
logger.addHandler(fileHandler)

#Send logs to laptop
socketHandler = logging.handlers.SocketHandler('127.0.0.1', logging.handlers.DEFAULT_TCP_LOGGING_PORT)
logger.addHandler(socketHandler)
 
start_sensors()

server_listen_forever()