import sys
import logging
from datetime import datetime

from shared.customlogging.handler import MakeFileHandler
from shared.customlogging.filter import SensorFilter

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
fileHandler = MakeFileHandler("logs/laptop/"+datetime.now().strftime("laptop_%Y-%m-%d %H-%M-%S.log"))
fileHandler.setFormatter(loggingFormat)
fileHandler.addFilter(loggingFilter)
logger.addHandler(fileHandler)
