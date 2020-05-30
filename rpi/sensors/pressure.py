import logging
import threading
import glob
import os
import time
import SMbus
import struct

from rpi.sensors.sensorlogging import SensorLogging

class Pressure:
    bus = smbus.SMBus(1)
    device_ID = 0xBB          #device_id
    address = 0b1011100        #slave address of device

    CTRL_REG0 = 0x20        #control Register addresses
    CTRL_REG3 = 0x23

    PRESS_OUT_XL = 0x28     #lower part of reference pressure (bits 0-7)
    PRESS_OUT_L = 0x29      #middle part of reference pressure (bits 8-15)
    PRESS_OUT_H = 0x2A      #higher part of reference pressure (bits 16-23)


    def __init__(self, identity, sensorlogger):
        self.device_file = '/sys/bus/i2c/devices' + identity + '/i2c_slave1'
        self.sensorlogger = sensorlogger
        self.logger = logging.getLogger (__name__)

        if identity == Pressure.address:
            self.name = 'MEX-1031'
        else:
            self.logger.warning("Pressure sensor with address {} is not recognized.".format(identity))
            self.name = 'UNDEFINED'

    def initialize_pressure(self):
        bus.write_byte_data (self.address, self.CTRL_REG0, 0b00000010)
        time.sleep(0.5)
        #activate ENABLE_MEAS and set output data rates (table 16)
        bus.write_byte_data (self.address, self.CTRL_REG3, 0b01110000)
        bus.write_byte_data (self.address, self.CTRL_REG0, 0b00000000)
        time.sleep(0.5)

    #need to loop over this method
    def read_pressure(self):
        bus.write_byte_data (self.address, self.CTRL_REG0, 0b00000011)
        time.sleep(0.1) # Wait for the measurement to be done

        data0 = bus.read_byte_data(self.address, self.PRESS_OUT_XL)
        data1 = bus.read_byte_data(self.address, self.PRESS_OUT_L)
        data2 = bus.read_byte_data(self.address, self.PRESS_OUT_H)

        #convert data
        if data2 & (1 << 7):
            filler = 0xFF
        else:
            filler = 0x00

        # 2s comp notation ">i", ">" says to use Big Endian, and the "i" says it is$
        pressure = struct.unpack(">i", bytes([filler,data2,data1,data0]))[0]
        #The LSB represents 1/64 of a Pascal
        pressure /= 64
        return(pressure)

#what is this doing
    def logging_loop(self):
        inErrorState = False
        while True:
            try:
                self.sensorlogger.info([time.time()*1000, self.name, self.read()])

                if inErrorState:
                    inErrorState = False
                    self.logger.warning("Error has been cleared for {}".format(self.name))
            except OSError:
                if not inErrorState:
                    self.logger.exeption("Error while reading from {}".format(self.name))
                    inErrorState = True


class PressList(SensorLogging):
    def __init__ (self):
        super().__init__("pressure", ["value"])

    self.logger = logging.getLogger(__name__)

    while True:
        p = Pressure.read_pressure(address, self.sensorlogger)
        self.logger.debug("S")

    def logging_loop(self):
        for i in self.sensor_list:
            self.logger.debug("Starting {}".format(i.name))
            t = threading.Thread(target = i.logging_loop)
            t.daemon = True
            t.start()
