import logging
import math
import time
import tkinter as tk

SENSOR_REFRESH = 0.5


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

        self.last_update = 0

    def emit(self, record):
        if time.time() - self.last_update < SENSOR_REFRESH:
            return

        try:
            pressure = float(record.msg[1])

            self.value.config(text=round(pressure / 1000.0, 1))
            self.last_update = time.time()
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

        self.last_update = 0

    def emit(self, record):
        if time.time() - self.last_update < SENSOR_REFRESH:
            return

        try:
            accel_ms_x = float(record.msg[1])
            accel_ms_y = float(record.msg[2])
            accel_ms_z = float(record.msg[3])

            accel_ms = math.sqrt(accel_ms_x ** 2 + accel_ms_y ** 2 + accel_ms_z ** 2)

            accel_g = round(accel_ms / 9.8, 2)

            self.value.config(text=accel_g)
            self.last_update = time.time()
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

        self.current_colour = self.cget("background")

    def emit(self, record):
        heaterOn = record.heaterOn

        if heaterOn:
            self.value.config(text="Heating")
            self.set_bg_colour("green")
        else:
            self.value.config(text="Off")
            self.set_bg_colour(self.current_colour)

    def set_bg_colour(self, colour):
        self.config(bg=colour)
        self.title.config(bg=colour)
        self.value.config(bg=colour)


class ThermometerFrame(tk.Frame, logging.Handler):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightthickness=1, highlightbackground="black")
        logging.Handler.__init__(self)

        self.title = tk.Label(self, text="Temperature", font=("Arial", 18))
        self.title.grid(row=0, column=0)

        self.value = tk.Label(self, text="INVALID", font=("Arial", 18))
        self.value.grid(row=1, column=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Register a handler so we can get access to all the thermometer's data
        logging.getLogger("sensorlog.thermometer").addHandler(self)

        self.temperature_data = dict()

        self.set_bg_colour("red")

    def emit(self, record):
        device_id = record.msg[1]
        device_value = record.msg[2]

        # Update the temperature of the above sensor
        self.temperature_data[device_id] = device_value

        self.update_value()

    def update_value(self):
        sum = 0.0
        count = 0.0
        average_temp = None
        for i in self.temperature_data.values():
            try:
                sum += i
                count += 1
            except:
                pass

        if count > 0:
            average_temp = sum / count
            average_temp = round(average_temp, 2)

        motors = self.temperature_data.get("Motors")
        fan = self.temperature_data.get("Fan Intake")
        opposite = self.temperature_data.get("Opposite to Heater")
        electronics = self.temperature_data.get("Electronics")
        foam = self.temperature_data.get("Foam")

        self.value.config(text=f"Average: {average_temp}\nMotors: {motors}\nFan: {fan}\n"
                               f"Opposite to Heater: {opposite}\nElectronics: {electronics}\nFoam: {foam}")

        if 35 <= average_temp <= 39:
            self.set_bg_colour("green")
        else:
            self.set_bg_colour("red")

    def set_bg_colour(self, colour):
        self.config(bg=colour)
        self.title.config(bg=colour)
        self.value.config(bg=colour)


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

        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)

        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)
