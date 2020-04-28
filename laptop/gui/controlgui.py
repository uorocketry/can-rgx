import tkinter as tk
import logging

from laptop.gui.statusframe import StatusFrame


class ControlGUI:
    def __init__(self, master):
        master.title("Control")
        master.geometry("1000x200")

        self.status = StatusFrame(master)
        self.status.grid(row=0, sticky="nsew")



        master.grid_columnconfigure(0, weight=1)
        
        master.grid_rowconfigure(0, weight=1)




