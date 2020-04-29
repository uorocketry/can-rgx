import tkinter as tk
import logging

class StatusHandler(logging.Handler):
    def __init__(self, frame):
        '''
        frame: StatusFrame to update
        '''
        super().__init__()

        self.frame = frame

    def emit(self, record):
        self.frame.update_status(record.levelno)

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

        #Make the status fill most of the frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
    def update_status(self, status):
        if self.currentlevel > status:
            return

        self.flash = False
        if status == logging.WARNING:
            self.color = "blue"
            self.flash = True
        elif status == logging.ERROR:
            self.color = "red"
            self.flash = True

        self.currentlevel = status
        self.status.config(bg=self.color)
        if self.flash:
            self.parent.after(500, self.flash_status, 0)

    def flash_status(self, i):
        if not self.flash:
            return

        if i == 0:
            self.status.config(bg="white")
        else:
            self.status.config(bg=self.color)

        self.parent.after(500, self.flash_status, 1 if i == 0 else 0)

    def clear_status(self):
        self.currentlevel = logging.INFO
        self.color = "green"
        self.status.config(bg=self.color)
        self.flash = False

