import logging
import threading
import time
import tkinter as tk
import tkinter.messagebox

from laptop.network.client import send_message
from shared.motor import MotorDirection
from shared.network.requesttypes import RequestTypes


class MotorFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.label = tk.Label(self, text="Motor Control")
        self.label.grid(row=0, column=0, rowspan=2)

        for i in range(2):
            elem_up = tk.Button(self, text=f"Motor {i + 1} Up", command=lambda i=i: self.confirmation(i, MotorDirection.UP))
            elem_down = tk.Button(self, text=f"Motor {i + 1} Down", command=lambda i=i: self.confirmation(i, MotorDirection.DOWN))

            elem_up.grid(row=0, column=i + 1, sticky="nsew")
            elem_down.grid(row=1, column=i + 1, sticky="nsew")

            self.grid_columnconfigure(i + 1, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def confirmation(self, i, motor_direction):
        direction_string = "up" if motor_direction == MotorDirection.UP else "down"

        confirm = tkinter.messagebox.askokcancel("Confirmation",
                                                 "Are you sure you want to activate {} {} {}?".format("Motor",
                                                                                                      i + 1,
                                                                                                      direction_string))

        if confirm:
            self.activate_element(i, motor_direction)

    def activate_element(self, index, motor_direction):
        message = {'type': RequestTypes.CONTROLMOTOR, 'motorNumber': index, 'motorDirection': motor_direction}
        send_message(message)


class LEDFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.elementName = "LED"

        self.label = tk.Label(self, text="{} Control".format(self.elementName))
        self.label.grid(row=0, column=0)

        self.keys = ['a', 's', 'd', 'f', 'g', 'h', 'j']

        for i in range(7):
            elem = tk.Button(self, text="{} {} ({})".format(self.elementName, i + 1, self.keys[i]),
                             command=lambda i=i: self.confirmation(i))
            elem.grid(row=0, column=i + 1, sticky="nsew")
            self.grid_columnconfigure(i + 1, weight=1)

        self.grid_rowconfigure(0, weight=1)

        parent.bind("<Key>", func=self.key_press)

    def key_press(self, keypress):
        try:
            char = keypress.char

            i = self.keys.index(char)

            self.confirmation(i)
        except ValueError:
            pass

    def confirmation(self, i):
        confirm = tkinter.messagebox.askokcancel("Confirmation",
                                                 f"Are you sure you want to activate {self.elementName} {i + 1}?",
                                                 parent=self.parent)

        if confirm:
            threading.Thread(target=self.activate_element, args=(i,)).start()

    def activate_element(self, index):
        logger = logging.getLogger(__name__)

        countdown = 5
        while countdown > 0:
            logger.info(f"LED {index + 1}: {countdown}")
            time.sleep(1)
            countdown -= 1

        message = {'type': RequestTypes.CONTROLLED, 'ledNumber': index + 1}
        send_message(message)
