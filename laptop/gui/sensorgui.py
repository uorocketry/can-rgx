import logging
import tkinter as tk


class ThermometerFrame(tk.Frame, logging.Handler):
    def __init__(self, parent):
        super().__init__(parent, highlightthickness=1, highlightbackground="black")

        self.title = tk.Label(self, text="Average Temperature", font=("Arial", 18))
        self.title.grid(row=0, column=0)

        self.value = tk.Label(self, text="INVALID", font=("Arial", 18))
        self.value.grid(row=1, column=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Register a handler so we can get access to all the thermometer's data
        logging.getLogger("sensorlog.thermometer").addHandler(self)

        self.temperature_data = dict()

    def emit(self, record):
        device_id = record.msg[1]
        device_value = record.msg[2]

        # Update the temperature of the above sensor
        self.temperature_data[device_id] = device_value

        self.update_value()

    def update_value(self):
        average_temp = sum(self.temperature_data.values()) / float(len(self.temperature_data))

        self.value.config(text=average_temp)


class VibrationFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, highlightthickness=1, highlightbackground="black")

        self.label = tk.Label(self, text="Maximum Vibration", font=("Arial", 18))
        self.label.grid(row=0, column=0)

        self.label = tk.Label(self, text="INVALID", font=("Arial", 18))
        self.label.grid(row=1, column=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)


class SensorGUI:
    def __init__(self, master):
        self.master = master

        master.title("Sensors")
        master.geometry("500x500")

        self.thermometer = ThermometerFrame(master)
        self.thermometer.grid(row=0, column=0)

        self.thermometer = VibrationFrame(master)
        self.thermometer.grid(row=0, column=1)

        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)

        master.grid_rowconfigure(0, weight=1)
