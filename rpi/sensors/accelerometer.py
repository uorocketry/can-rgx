import time

import spidev

from rpi.sensors.sensorlogging import SensorLogging
from shared.customlogging.errormanager import ErrorManager


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val


# registers index
DATA_FORMAT = 0x31  # clear bit d6 for 4 wire, set for 3 wire
BW_RATE = 0x2C  # date and power mode control
POWER_CTL = 0x2D  # power saving features control
FIFO_CTL = 0x38  # FIFO mode select
INT_SOURCE = 0x30

DATA_X0 = 0x32  # x-axis data0
DATA_X1 = 0x33  # x-axis data1
DATA_Y0 = 0x34  # y-axis data0
DATA_Y1 = 0x35  # y-axis data1
DATA_Z0 = 0x36  # z-axis data0
DATA_Z1 = 0x37  # z-axis data1

# SPI config
SPI_MAX_CLOCK_HZ = 1600000  # 1.6MHz
SPI_MODE = 0b11
SPIBus = 0
SPIDevice = 0  # vib on 1, acc on 0
CSHIGH = False  # cs pin low at start of transmission

# Data Range
RANGE_2G = 0b00  # full resolution (10bits) , left-justified MSB mode, +/- 2g
RANGE_4G = 0b01  # full resolution (11bits), MSB mode, +/- 4g
RANGE_8G = 0b10  # full resolution(12bits), MSB mode, +/-8g
RANGE_16G = 0b01  # full resolution(13bits), MSB mode, +/-16g
# self test:
SELF_TEST = 0b10001111  # full resolution (13bits) MSB mode, +/-16g

# register values
MEASURE_MODE = 0b00001000  # set device to measure mode (D3)
BW_OUTPUT_RATE = 0x0B  # normal operation, 3200Hz output rate, 1600Hz bandwidth
FIFO_MODE = 0b10000001  # stream mode, INT1 triggered, 31bit buffer
FIFO_BYPASS = 0b00000000
READ_BIT = 0x01
WRITE_BIT = 0x00
DUMMY_BYTE = 0x00
SEQUENTIAL_READ_BYTE = 0b11

# Conversion factors
CONV_FULLR = 0.004  # applicable for all gs
EARTH_GRAVITY = 9.80665

# Precision of the output, how many decimals to keep
OUTPUT_PRECISION = 3


class Accelerometer(SensorLogging):
    def setup(self, measure_range=RANGE_16G):
        self.spi = spidev.SpiDev()
        self.spi.open(SPIBus, SPIDevice)
        self.spi.max_speed_hz = SPI_MAX_CLOCK_HZ
        self.spi.mode = SPI_MODE

        self.check_sensor_connection()
        self.set_measure_range(measure_range)
        self.set_fifo()
        self.set_bw_rate()
        self.enable_measure_mode()

    def check_sensor_connection(self):
        """
        Checks if the correct sensor is connected, or if anything is connected
        at all. If the sensor is not connected, an error will be logged and this
        function will block until it connects.
        """
        em = ErrorManager(__name__)

        DEVICE_ID = 0xE5

        if self.xfer_read_byte(0x00) == DEVICE_ID:
            return

        em.error("Acceleration sensor is not connected", "ACCEL_CONNECTION")

        # Wait until the sensor connects
        while self.xfer_read_byte(0x00) != DEVICE_ID:
            pass

        em.resolve("Acceleration sensor connected", "ACCEL_CONNECTION")

    def set_measure_range(self, measure_range):
        """Function to set range and resolution"""
        self.xfer_write_byte(DATA_FORMAT | 0b1000, measure_range)

    def set_fifo(self):
        """Function to set FIFO mode"""
        self.xfer_write_byte(FIFO_CTL, FIFO_MODE)

    def set_bw_rate(self):
        """Function to set bandwidth and output data rate"""
        self.xfer_write_byte(BW_RATE, BW_OUTPUT_RATE)

    def enable_measure_mode(self):
        """Function to activate ADLX343 and initiate measurement"""
        self.xfer_write_byte(POWER_CTL, MEASURE_MODE)

    def xfer_write_byte(self, address, value):
        """SPI function to write bytes, set MSB low"""
        self.spi.xfer2([(address & ~(1 << 7)), value & 0XFF])

    def xfer_read_byte(self, address):
        """"FIX THIS  'list' and 'int' error SPI function to read bytes, set MSB high to read"""
        retval = self.spi.xfer2([(address | READ_BIT << 7), 0x00])[1]
        return retval

    def xfer_read_multiple_bytes_sequential(self, start_address, n):
        spi_read = [start_address | (SEQUENTIAL_READ_BYTE << 6)]
        for _ in range(n):
            spi_read.append(DUMMY_BYTE)
        retlist = self.spi.xfer2(spi_read)[1:]
        return retlist

    def wait_until_data_ready(self):
        """Block here until the sensor has new data"""
        ready = 0
        while ready == 0:
            int_source = self.xfer_read_byte(INT_SOURCE)
            ready = (int_source >> 7) & 0x1  # Check the DATA_READY bit

    def get_acceleration_data(self):
        """
        Return the acceleration of each axis in m/s^2
        The return value is a map of the format {"x": x_data, "y": y_data, "z": z_data}
        """
        raw_axes = self.xfer_read_multiple_bytes_sequential(start_address=DATA_X0, n=6)

        # Combine data
        x_data = (raw_axes[1] << 8) | raw_axes[0]
        y_data = (raw_axes[3] << 8) | raw_axes[2]
        z_data = (raw_axes[5] << 8) | raw_axes[4]

        # Apply 2s comp
        x_data = twos_comp(x_data, 16)
        y_data = twos_comp(y_data, 16)
        z_data = twos_comp(z_data, 16)

        # Convert to m/s^2
        x_data *= CONV_FULLR * EARTH_GRAVITY
        y_data *= CONV_FULLR * EARTH_GRAVITY
        z_data *= CONV_FULLR * EARTH_GRAVITY

        # Round the values
        x_data = round(x_data, OUTPUT_PRECISION)
        y_data = round(y_data, OUTPUT_PRECISION)
        z_data = round(z_data, OUTPUT_PRECISION)

        return {"x": x_data, "y": y_data, "z": z_data}

    def run(self):
        super().setup_logging("acceleration", ["x", "y", "z"])

        self.setup()
        while True:
            self.wait_until_data_ready()
            val = self.get_acceleration_data()
            self.sensorlogger.info([time.time() * 100, val["x"], val["y"], val["z"]])
