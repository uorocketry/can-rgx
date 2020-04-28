import tkinter as tk
import logging

from laptop.gui.statusframe import StatusFrame
from laptop.gui.controlframe import MotorFrame, LEDFrame


class ControlGUI:
    def __init__(self, master):
        master.title("Control")
        master.geometry("1000x200")

        self.status = StatusFrame(master)
        self.status.grid(row=0, sticky="nsew")

        self.motor = MotorFrame(master)
        self.motor.grid(row=1, sticky="nsew", pady=20)

        self.motor = LEDFrame(master)
        self.motor.grid(row=2, sticky="nsew")

        master.grid_columnconfigure(0, weight=1)
        
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)




