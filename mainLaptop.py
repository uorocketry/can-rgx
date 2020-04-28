import sys
import logging
from datetime import datetime
import tkinter as tk
import tkinter.messagebox

from shared.customlogging.handler import MakeFileHandler
from shared.customlogging.filter import SensorFilter
import laptop.gui.logginggui as logginggui
import laptop.gui.controlgui as controlgui
import laptop.gui.statusframe as statusframe

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

#Setup Logging for the GUI
root = tk.Tk()

logGUI = logginggui.LoggingGUI(root)
guiHandler = logginggui.LoggingGUIHandler(logGUI)
guiHandler.setFormatter(loggingFormat)
guiHandler.addFilter(loggingFilter)
logger.addHandler(guiHandler)


#Setup the GUI for controlling the experiment
window2 = tk.Toplevel(root)
controlGUI = controlgui.ControlGUI(window2)

#Setup the status display
statusHandler = statusframe.StatusHandler(controlGUI.status)
statusHandler.setFormatter(loggingFormat)
statusHandler.addFilter(loggingFilter)
logger.addHandler(statusHandler)

root.mainloop()
