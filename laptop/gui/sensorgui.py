import logging
import math
import operator
import tkinter as tk


class VibrationFrame(tk.Frame, logging.Handler):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightthickness=1, highlightbackground="black")
        logging.Handler.__init__(self)

        self.title = tk.Label(self, text="Max Vibration", font=("Arial", 18))
        self.title.grid(row=0, column=0)

        self.value = tk.Label(self, text="INVALID", font=("Arial", 18))
        self.value.grid(row=1, column=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Register a handler so we can get access to all the thermometer's data
        logging.getLogger("sensorlog.vibration").addHandler(self)

        self.current_time = 0
        self.vibration_data = dict()

    def emit(self, record):
        try:
            time = record.msg[0]
            frequency = float(record.msg[2])
            x_data = float(record.msg[3])
            y_data = float(record.msg[4])
            z_data = float(record.msg[5])

            # We are doing a new batch of vibration data, so update value than clear the data
            if time != self.current_time:
                self.update_value()

                self.vibration_data = dict()
                self.current_time = time

            # Add the current value to the dict
            amplitude = math.sqrt(x_data**2 + y_data**2 + z_data**2)

            self.vibration_data[frequency] = amplitude
        except:
            pass

    def update_value(self):
        max_value = max(self.vibration_data.items(), key=operator.itemgetter(1))

        self.value.config(text=f"Frequency: {max_value[0]}\nAmplitude: {max_value[1]}")


class PressureFrame(tk.Frame, logging.Handler):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightthickness=1, highlightbackground="black")
        logging.Handler.__init__(self)

        self.title = tk.Label(self, text="Pressure", font=("Arial", 18))
        self.title.grid(row=0, column=0)

        self.value = tk.Label(self, text="INVALID", font=("Arial", 18))
        self.value.grid(row=1, column=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Register a handler so we can get access to all the thermometer's data
        logging.getLogger("sensorlog.pressure").addHandler(self)

    def emit(self, record):
        try:
            pressure = float(record.msg[1])

            self.value.config(text=pressure)
        except:
            pass


class AccelerationFrame(tk.Frame, logging.Handler):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightthickness=1, highlightbackground="black")
        logging.Handler.__init__(self)

        self.title = tk.Label(self, text="Accelerometer", font=("Arial", 18))
        self.title.grid(row=0, column=0)

        self.value = tk.Label(self, text="INVALID", font=("Arial", 18))
        self.value.grid(row=1, column=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Register a handler so we can get access to all the thermometer's data
        logging.getLogger("sensorlog.acceleration").addHandler(self)

    def emit(self, record):
        try:
            accel_ms_x = float(record.msg[1])
            accel_ms_y = float(record.msg[2])
            accel_ms_z = float(record.msg[3])

            accel_ms = math.sqrt(accel_ms_x ** 2 + accel_ms_y ** 2 + accel_ms_z ** 2)

            self.value.config(text=accel_ms / 9.8)
        except:
            pass


class HeaterFrame(tk.Frame, logging.Handler):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightthickness=1, highlightbackground="black")
        logging.Handler.__init__(self)

        self.title = tk.Label(self, text="Heater State", font=("Arial", 18))
        self.title.grid(row=0, column=0)

        self.value = tk.Label(self, text="INVALID", font=("Arial", 18))
        self.value.grid(row=1, column=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        logging.getLogger("sensorlog.temp_management").addHandler(self)

    def emit(self, record):
        heaterOn = record.heaterOn

        if heaterOn:
            self.value.config(text="Heating")
        else:
            self.value.config(text="Off")


class ThermometerFrame(tk.Frame, logging.Handler):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightthickness=1, highlightbackground="black")
        logging.Handler.__init__(self)

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
        sum = 0.0
        count = 0.0
        for i in self.temperature_data.values():
            try:
                sum += i
                count += 1
            except:
                pass

        if count > 0:
            average_temp = sum / count

            self.value.config(text=average_temp)


class SensorGUI:
    def __init__(self, master):
        self.master = master

        master.title("Sensors")
        master.geometry("500x500")

        self.thermometer = ThermometerFrame(master)
        self.thermometer.grid(row=0, column=0)

        self.heater = HeaterFrame(master)
        self.heater.grid(row=0, column=1)

        self.accel = AccelerationFrame(master)
        self.accel.grid(row=1, column=0)

        self.pressure = PressureFrame(master)
        self.pressure.grid(row=1, column=1)

        self.vibration = VibrationFrame(master)
        self.vibration.grid(row=2, column=0)

        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)

        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)
