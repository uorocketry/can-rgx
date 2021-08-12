import struct
import time
import smbus
from rpi.sensors.sensorlogging import SensorLogging
from shared.customlogging.errormanager import ErrorManager

PRES_SENS_ADDRESS = 0x76 #SDO to GND

#Registers Index
CMD = 0x7E
CONFIG = 0x1F
PWR_CTRL = 0x1B
IF_CONF = 0x1A
FIFO_CONFIG1 = 0x17
FIFO_CONFIG2 = 0x18
ODR = 0x1D
OSR = 0x1C

DATA0 = 0x04    #Pressure bits 7-0
DATA1 = 0x05    #Pressure 15-8
DATA2 = 0x06    #Pressure 23-16

DATA3_T = 0x07  #Temp bits 7-0
DATA4_T = 0x08  #Temp 15-8
DATA5_T = 0x09  #Temp 23-16


READ_BIT = 0x01
WRITE_BIT = 0X00
DUMMY_BYTE = 0X00

#Register Values
POWER_MODE = 0b00001111     #Enable pressure and temp. measurement, normal mode
ODR_MODE = 0x00             #Output data rate 200Hz (lowest) - Change as required


class Pressure(SensorLogging):
    def setup(self):
        self.bus = smbus.SMBus(1)

        self.check_sensor_connection()
        self.set_power_mode()
        self.set_output_data_rate()

    def check_sensor_connection(self):
        em = ErrorManager(__name__)

        DEVICE_ID = 0x50

        if self.bus.read_byte_data(PRES_SENS_ADDRESS, 0x00) == DEVICE_ID:
            return

        em.error("Acceleration sensor is not connected", "ACCEL_CONNECTION")

        # Wait until the sensor connects
        while self.bus.read_byte_data(PRES_SENS_ADDRESS, 0x00) != DEVICE_ID:
            pass

    def set_power_mode(self):
        """Method to enable sensor and set Power mode"""
        self.bus.write_byte_data(PRES_SENS_ADDRESS, PWR_CTRL, POWER_MODE)

    def set_output_data_rate(self):
        """Method to set output data rate"""
        self.bus.write_byte_data(PRES_SENS_ADDRESS, ODR, ODR_MODE)





    def read_pressure(self):
        pass






    def run(self):
        super().setup_logging("pressure", ["value"])
        self.setup()

        em = ErrorManager(__name__)
        while True:
            try:
                self.sensorlogger.info([time.time() * 1000, self.read_pressure()])

                em.resolve("Error has been cleared for pressure sensor", "pressure")
            except OSError as e:
                em.error("Error while reading from pressure sensor", "pressure")