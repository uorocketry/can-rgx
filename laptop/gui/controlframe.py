import tkinter as tk
import tkinter.messagebox

from laptop.network.client import send_message
from shared.network.requesttypes import RequestTypes


class GeneralControlFrame(tk.Frame):
    def __init__(self, parent, elementName, amount):
        super().__init__(parent)

        self.elementName = elementName

        self.label = tk.Label(self, text="{} Control".format(elementName))
        self.label.grid(row=0, column=0)

        for i in range(amount):
            elem = tk.Button(self, text="{} {}".format(elementName, i + 1), command=lambda i=i: self.confirmation(i))
            elem.grid(row=0, column=i + 1, sticky="nsew")
            self.grid_columnconfigure(i + 1, weight=1)

        self.grid_rowconfigure(0, weight=1)

    def confirmation(self, i):
        confirm = tkinter.messagebox.askokcancel("Confirmation",
                                                 "Are you sure you want to activate {} {}?".format(self.elementName,
                                                                                                   i + 1))

        if confirm:
            self.activate_element(i)

    def activate_element(self, index):
        raise NotImplementedError


class MotorFrame(GeneralControlFrame):
    def __init__(self, parent):
        super().__init__(parent, "Motor", 2)


class LEDFrame(GeneralControlFrame):
    def __init__(self, parent):
        super().__init__(parent, "LED", 7)

    def activate_element(self, index):
        message = {'type': RequestTypes.CONTROLLED, 'ledNumber': index + 1}
        send_message(message)
