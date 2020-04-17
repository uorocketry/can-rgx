import sys
import logging
from datetime import datetime
from shared.customlogging.handler import MakeFileHandler

#Setting up logging to console and file

logger = logging.getLogger("rpi")
logger.setLevel(logging.INFO)

loggingFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#Logging to console
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(loggingFormat)
logger.addHandler(consoleHandler)

#Logging to file. A new file is created each run, with the name being the current date and time
fileHandler = MakeFileHandler("logs/main/"+datetime.now().strftime("log_%Y-%m-%d %H-%M-%S.log"))
fileHandler.setFormatter(loggingFormat)
logger.addHandler(fileHandler)
