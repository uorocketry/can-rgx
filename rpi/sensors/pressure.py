import logging
import struct
import time

import smbus

from rpi.sensors.sensorlogging import SensorLogging


class Pressure(SensorLogging):
    device_ID = 0xBB  # device_id
    address = 0b1011100  # slave address of device

    CTRL_REG0 = 0x20  # control Register addresses
    CTRL_REG3 = 0x23

    PRESS_OUT_XL = 0x28  # lower part of reference pressure (bits 0-7)
    PRESS_OUT_L = 0x29  # middle part of reference pressure (bits 8-15)
    PRESS_OUT_H = 0x2A  # higher part of reference pressure (bits 16-23)

    def setup(self):
        self.bus = smbus.SMBus(1)
        self.bus.write_byte_data(self.address, self.CTRL_REG0, 0b00000010)
        time.sleep(0.5)
        # activate ENABLE_MEAS and set output data rates (table 16)
        self.bus.write_byte_data(self.address, self.CTRL_REG3, 0b01110000)
        self.bus.write_byte_data(self.address, self.CTRL_REG0, 0b00000000)
        time.sleep(0.5)

    def read_pressure(self):
        self.bus.write_byte_data(self.address, self.CTRL_REG0, 0b00000011)
        time.sleep(0.1)  # Wait for the measurement to be done

        data0 = self.bus.read_byte_data(self.address, self.PRESS_OUT_XL)
        data1 = self.bus.read_byte_data(self.address, self.PRESS_OUT_L)
        data2 = self.bus.read_byte_data(self.address, self.PRESS_OUT_H)

        # convert data
        if data2 & (1 << 7):
            filler = 0xFF
        else:
            filler = 0x00

        # 2s comp notation ">i", ">"  use Big Endian
        pressure = struct.unpack(">i", bytes([filler, data2, data1, data0]))[0]
        # LSB represents 1/64 of a Pascal
        pressure /= 64
        return pressure

    def run(self):
        super().setup_logging("pressure", ["value"])
        self.setup()

        logger = logging.getLogger(__name__)

        inErrorState = False
        while True:
            try:
                self.sensorlogger.info([time.time() * 1000, self.read_pressure()])

                if inErrorState:
                    inErrorState = False
                    logger.warning("Error has been cleared for pressure sensor.")
            except OSError:
                if not inErrorState:
                    logger.exception("Error while reading from pressure sensor.")
                    inErrorState = True
