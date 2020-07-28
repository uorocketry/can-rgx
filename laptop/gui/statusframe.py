import logging
import tkinter as tk


class StatusFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.color = "green"
        self.status = tk.Label(self, text="Status", bg=self.color)
        self.status.grid(row=0, column=0, sticky="nsew")
        self.flash = False

        self.clear = tk.Button(self, text="Clear", command=self.clear_status)
        self.clear.grid(row=0, column=1, sticky="nsew")
        self.currentlevel = logging.INFO

        # Make the status fill most of the frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Track which error have been raised so they can be cleared automatically
        # Each key is a string representing the error ID, and the value is the error level
        self.errorIDs = dict()

    def update_status(self, record):
        '''
        Updates the status display from the record.
        Returns if the record cleared an existing error.
        '''
        level = record.levelno

        clearedError = False
        if level >= logging.WARNING:
            if not hasattr(record, 'errorID'):  # Pass default errorID to error if there is none
                record.errorID = 'unamed'

                # Only update if the level of this record is higher than what is currently registered
            if record.errorID not in self.errorIDs or (
                    record.errorID in self.errorIDs and level > self.errorIDs[record.errorID]):
                self.errorIDs[record.errorID] = level
        elif hasattr(record, 'errorID'):
            i = self.errorIDs.pop(record.errorID,
                                  None)  # If the info message has a errorID, automatically clear the error if there is one
            clearedError = i is not None

        # Next lines find the error with the highest level in the list
        highestlevel = logging.INFO
        highestcolor = 'green'
        highestflash = False
        for _, errorLevel in self.errorIDs.items():
            if errorLevel > highestlevel:
                highestlevel = errorLevel

                if errorLevel == logging.WARNING:
                    highestcolor = "blue"
                elif errorLevel >= logging.ERROR:
                    highestcolor = "red"
                    highestflash = True

        self.color = highestcolor
        self.currentlevel = highestlevel
        self.status.config(bg=highestcolor)
        if not self.flash and highestflash:
            self.flash = True
            self.parent.after(500, self.flash_status, 0)

        return clearedError

    def flash_status(self, i):
        if not self.flash:
            return

        if i == 0:
            self.status.config(bg="white")
        else:
            self.status.config(bg=self.color)

        self.parent.after(500, self.flash_status, 1 if i == 0 else 0)

    def clear_status(self):
        self.errorIDs.clear()
        self.currentlevel = logging.INFO
        self.color = "green"
        self.status.config(bg=self.color)
        self.flash = False
