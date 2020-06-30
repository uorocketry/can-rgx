import logging
import sys
import threading
import tkinter as tk
import tkinter.messagebox

import laptop.gui.controlgui as controlgui
import laptop.gui.logginggui as logginggui
from laptop.network.loggingreceiver import logging_receive_forever
from laptop.network.pingchecker import PingChecker
from shared.customlogging.filter import SensorFilter
from shared.customlogging.handler import MakeFileHandler

# Setting up logging to console and file

logger = logging.getLogger()
logger.setLevel(logging.INFO)

loggingFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
loggingFormatConsole = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%H:%M:%S')
loggingFilter = SensorFilter()

# Logging to console
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(loggingFormat)
consoleHandler.addFilter(loggingFilter)
logger.addHandler(consoleHandler)

# Logging to file. A new file is created each run, with the name being the current date and time
fileHandler = MakeFileHandler('laptop', 'main')
fileHandler.setFormatter(loggingFormat)
fileHandler.addFilter(loggingFilter)
logger.addHandler(fileHandler)

# Seting up of the GUI
root = tk.Tk()

# Setup the GUI for controlling the experiment
window2 = tk.Toplevel(root)
controlGUI = controlgui.ControlGUI(window2)

# Setup the logging window
logGUI = logginggui.LoggingGUI(root)
guiHandler = logginggui.LoggingGUIHandler(logGUI, controlGUI.status)
guiHandler.setFormatter(loggingFormatConsole)
guiHandler.addFilter(loggingFilter)
logger.addHandler(guiHandler)

# Start the log receiver
t = threading.Thread(target=logging_receive_forever)
t.setDaemon(True)
t.start()

# Start the ping daemon
PingChecker().start()


# Add confirmation box on closing
def close_application():
    close = tkinter.messagebox.askokcancel("Quit", "Are you sure you want to quit?")
    if close:
        root.destroy()


root.protocol("WM_DELETE_WINDOW", close_application)
window2.protocol("WM_DELETE_WINDOW", close_application)

root.mainloop()
