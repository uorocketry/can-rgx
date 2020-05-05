import tkinter as tk
import tkinter.scrolledtext as tkst
import logging

class LoggingGUIHandler(logging.Handler):
    def __init__(self, loggingGUI, statusFrame):
        '''
        loggingGui: instance of LoggingGUI to send messages to 
        statusFrame: statusFrame to update
        '''
        super().__init__()
        self.gui = loggingGUI
        self.status = statusFrame

    def emit(self, record):
        clearedError = self.status.update_status(record)
        self.gui.write_message(self.format(record), record.levelname, clearedError)
        


class LoggingGUI:
    def __init__(self, master):
        self.master = master

        master.title("Logs")
        master.geometry("1000x400")

        #Configure text area
        self.text = tkst.ScrolledText(master)
        self.text.grid(row=1, column=0, stick="nsew")
        self.text.config(state=tk.DISABLED)

        #Checkbox to control if we scroll down automatically
        self.keepDown = tk.IntVar(value=1)
        c = tk.Checkbutton(master, text="Scroll automatically", variable=self.keepDown)
        c.grid(row=0, column=0, stick="w")

        #To make sure everything scales when the window size changes
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)

        #Define colors for the various logging levels
        self.text.tag_config("CLEARERROR", foreground="green")
        self.text.tag_config("DEBUG", foreground="black")
        self.text.tag_config("INFO", foreground="black")
        self.text.tag_config("WARNING", foreground="blue")
        self.text.tag_config("ERROR", foreground="red")


    def write_message(self, log, loggingLevel, clearedError):
        if clearedError:
            loggingLevel = "CLEARERROR"
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, log + "\n", loggingLevel)
        if self.keepDown.get() == 1:
            self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

