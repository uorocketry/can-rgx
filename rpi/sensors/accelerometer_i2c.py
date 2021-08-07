import time
import smbus
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

# Data Range
RANGE_2G = 0b00  # 10 bit res, right-justified LSB mode, +/- 2g
RANGE_4G = 0b01  # 10 bit res, LSB mode, +/- 4g
RANGE_8G = 0b10  # 10 bit res, LSB mode, +/-8g
RANGE_16G = 0b11  # 10 bit res, LSB mode, +/-16g
# self test:
SELF_TEST = 0b10001111  # full resolution (13bits) MSB mode, +/-16g

# register values
MEASURE_MODE = 0b00001000  # set device to measure mode (D3)
BW_OUTPUT_RATE = 0b00001011  # normal operation, 200Hz output rate (max for 100kHz RPi I2C)
FIFO_MODE = 0b10000001  # stream mode, INT1 triggered, 31bit buffer
FIFO_BYPASS = 0b00000000

# I2C specific read/write with ALT ADDRESS pin high
READ_BIT = 0x3B
WRITE_BIT = 0x3A
DUMMY_BYTE = 0x00

# Conversion factors
CONV_FULLR = 0.004  # applicable for all gs
EARTH_GRAVITY = 9.80665

# Precision of the output, how many decimals to keep
OUTPUT_PRECISION = 3

# I2C Config
ACC_DEVICE_ID = 0xE5
ACC_ADDRESS = 0x53  # CORRECT THIS VALUE depending on physical connection (ALT ADDRESS LOW)


class Accelerometer(SensorLogging):
    def setup(self, measure_range=RANGE_16G):
        self.bus = smbus.SMBus(1)  # correct this too

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

        if self.bus.read_byte_data(ACC_ADDRESS, 0x00) == ACC_DEVICE_ID:
            return

        em.error("Acceleration sensor is not connected", "ACCEL_CONNECTION")

        # Wait until the sensor connects
        while self.bus.read_byte_data(ACC_ADDRESS, 0x00) != ACC_DEVICE_ID:
            pass

        em.resolve("Acceleration sensor connected", "ACCEL_CONNECTION")

    def set_measure_range(self, measure_range):
        """Method to set range and resolution"""
        self.bus.write_byte_data(ACC_ADDRESS, DATA_FORMAT | 0b1000, measure_range)

    def set_fifo(self):
        """Method to set FIFO mode"""
        self.bus.write_byte_data(ACC_ADDRESS, FIFO_CTL, FIFO_MODE)

    def set_bw_rate(self):
        """Method to set bandwidth and output data rate"""
        self.bus.write_byte_data(ACC_ADDRESS, BW_RATE, BW_OUTPUT_RATE)

    def enable_measure_mode(self):
        """Method to activate ADXL343 and initiate measurement"""
        self.bus.write_byte_data(ACC_ADDRESS, POWER_CTL, MEASURE_MODE)

    def get_acceleration_data(self):
        """Return acceleration of each axis in m/s^2"""
        x_data0 = self.bus.read_byte_data(ACC_ADDRESS, DATA_X0)
        x_data1 = self.bus.read_byte_data(ACC_ADDRESS, DATA_X1)

        y_data0 = self.bus.read_byte_data(ACC_ADDRESS, DATA_Y0)
        y_data1 = self.bus.read_byte_data(ACC_ADDRESS, DATA_Y1)

        z_data0 = self.bus.read_byte_data(ACC_ADDRESS, DATA_Z0)
        z_data1 = self.bus.read_byte_data(ACC_ADDRESS, DATA_Z1)

        # Combine respective registers
        x_data = ((x_data1 & 0x03) * 256) + x_data0
        y_data = ((y_data1 & 0x03) * 256) + y_data0
        z_data = ((z_data1 & 0x03) * 256) + z_data0

        # Apply 2s comp
        x_data = twos_comp(x_data, 16)
        y_data = twos_comp(y_data, 16)
        z_data = twos_comp(z_data, 16)

        # Convert to m/s^2 and round
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
            acceleration = self.get_acceleration_data()
            print(acceleration)
            self.sensorlogger.info([time.time() * 100, acceleration["x"], acceleration["y"], acceleration["z"]])
