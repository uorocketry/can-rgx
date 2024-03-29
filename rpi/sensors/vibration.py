"""
Code for interacting with the ADCMXL3021BMLZ vibration sensor
"""

import logging
import time

import RPi.GPIO as GPIO
import spidev

from rpi.sensors.sensorlogging import SensorLogging

# Only bus 0 is available on RPi
SPIBus = 0
# Chip select. Either 0 or 1
SPIDevice = 1

# Sample rate to use. See table 20 in datasheet for details. Note: Table 89 has a possible error.
# Sample Rate = 220000 / 2^(AVG_CNT_Bit)
AVG_CNT_Bit = 7

# Number of FFT averages to do
FFTAverages = 1

# Pin connected to the BUSY output
BUSYPin = 5

# Registers from the sensor
PAGE_ID = 0x00
TEMP_OUT = 0x02
SUPPLY_OUT = 0x04
FFT_AVG1 = 0x06
FFT_AVG2 = 0x08
BUF_PNTR = 0x0A
REC_PNTR = 0x0C
X_BUF = 0x0E
Y_BUF = 0x10
Z_BUF = 0x12
RSS_BUF = 0x12
X_ANULL = 0x14
Y_ANULL = 0x16
Z_ANULL = 0x18
REC_CTRL = 0x1A
REC_PRD = 0x1E
ALM_F_LOW = 0x20
ALM_F_HIGH = 0x22
ALM_X_MAG1 = 0x24
ALM_Y_MAG1 = 0x26
ALM_X_MAG2 = 0x2A
ALM_Y_MAG2 = 0x2C
ALM_PNTR = 0x30
ALM_S_MAG = 0x32
ALM_CTRL = 0x34
DIO_CTRL = 0x36
FILT_CTRL = 0x38
AVG_CNT = 0x3A
DIAG_STAT = 0x3C
GLOB_CMD = 0x3E
ALM_X_STAT = 0x40
ALM_Y_STAT = 0x42
ALM_X_PEAK = 0x46
ALM_Y_PEAK = 0x48
TIME_STAMP_L = 0x4C
TIME_STAMP_H = 0x4E
REV_DAY = 0x52
YEAR_MON = 0x54
PROD_ID = 0x56
SERIAL_NUM = 0x58
USER_SCRATCH = 0x5A
REC_FLASH_CNT = 0x5C
MISC_CTRL = 0x64
REC_INFO1 = 0x66
REC_INFO2 = 0x68
REC_CNTR = 0x6A
ALM_X_FREQ = 0x6C
ALM_Y_FREQ = 0x6E
ALM_Z_FREQ = 0x70
STAT_PNTR = 0x72
X_STATISTIC = 0x74
Y_STATISTIC = 0x76
Z_STATISTIC = 0x78
FUND_FREQ = 0x7A
FLASH_CNT_L = 0x7C
FLASH_CNT_U = 0x7E


class FFTRecord:
    def __init__(self, lowestfrequency, binsize, x_data, y_data, z_data):
        self.lowestfrequency = lowestfrequency
        self.binsize = binsize
        self.x_data = x_data
        self.y_data = y_data
        self.z_data = z_data


# If using Pylint in IDE, for some reason warns about GPIO not
# having any members. The following line tells it to ignore this.
# pylint: disable=no-member
class Vibration(SensorLogging):
    """
    Class which interacts with an ADcmXL3021 vibration sensor.
    """

    def setup(self):
        # Keep track of raised errors
        self.errors = set()

        self.spi = spidev.SpiDev()
        self.spi.open(SPIBus, SPIDevice)

        # Configure the settings to communicate with the device
        self.spi.mode = 0b11
        self.spi.max_speed_hz = 14000000  # 14MHz
        self.spi.lsbfirst = False

        # Configure BUSY pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(BUSYPin, GPIO.IN)

        self.write_to_register(PAGE_ID, 0x0000)

        # Check if the sensor is connected, blocking here until it is
        self.check_sensor_connection(True)

        # Set Window settings to Hanning, use SR0, record mode to MFFT
        self.write_to_register(REC_CTRL, 0x1100)

        # Set sample rate. We only use SR0, and don't care about the rest
        self.write_to_register(AVG_CNT, AVG_CNT_Bit)

        # Spectral averaging. Again, only care about SR0
        self.write_to_register(FFT_AVG1, FFTAverages)

    def wait_for_sensor(self):
        """
        Blocks until sensor is ready
        """
        while not GPIO.input(BUSYPin):
            pass

    def __check_sensor(self, check):
        if check != 0x0BCD and "PROD_ID_Error" not in self.errors:
            logger = logging.getLogger(__name__)
            logger.error(
                f"PROD_ID is not the expected value: got {hex(check)} instead of 0x0BCD. Is the sensor plugged?"
                , extra={'errorID': f'VibrationPROD_ID'})
            self.errors.add("PROD_ID_Error")
        elif check == 0x0BCD and "PROD_ID_Error" in self.errors:
            logger = logging.getLogger(__name__)
            logger.info(f"Error cleared, PROD_ID is now the expected value.", extra={'errorID': f'VibrationPROD_ID'})
            self.errors.remove("PROD_ID_Error")

    def check_sensor_connection(self, block):
        """
        Checks if the correct sensor is connected, or if anything is connected
        at all by checking PROD_ID and comparing it to the expected value.

        If the returned value is not what is expected, an error will be logged.
        If block is True, this function will block until the correct value is returned.
        """

        check = self.read_from_register(PROD_ID)

        self.__check_sensor(check)

        while block and check != 0x0BCD:
            check = self.read_from_register(PROD_ID)
            self.__check_sensor(check)

    def __check_err_bit(self, stat, bit, message):
        if ((stat >> bit) & 0b1) and bit not in self.errors:
            logger = logging.getLogger(__name__)
            self.errors.add(bit)
            logger.warning("Error on sensor: " + message, extra={'errorID': f'VibrationBit{bit}'})
        elif not ((stat >> bit) & 0b1) and bit in self.errors:
            logger = logging.getLogger(__name__)
            self.errors.remove(bit)
            logger.info("Error cleared: " + message, extra={'errorID': f'VibrationBit{bit}'})

    def check_for_errors(self):
        """
        Check for errors and logs it if it is found.
        """
        self.wait_for_sensor()

        stat = self.read_from_register(DIAG_STAT)

        self.__check_err_bit(stat, 6, "Flash test result, checksum flag")
        self.__check_err_bit(stat, 5, "Self test diagnostic error flag.")
        self.__check_err_bit(stat, 4, "Recording escape flag.")
        self.__check_err_bit(stat, 3, "Self test diagnostic error flag.")
        self.__check_err_bit(stat, 2, "SPI communication failure (SCLKs ≠ even multiple of 16).")
        self.__check_err_bit(stat, 1, "Power supply > 3.625 V.")
        self.__check_err_bit(stat, 0, "Power supply < 2.975 V.")

    def write_to_register(self, address, data):
        """
        Write to the specified 16 bit wide register.

        Parameters
        ----------
        address: int
            7 bit address of the register. This is the address of register containing the MSB
        data: int
            16 bit of data to write
        """
        self.wait_for_sensor()

        # Send message in two parts, each containing 16 bits.
        # First bit is 1 for the write bit, followed by the 7 bit address
        # This is followed by the data, which has been splited accross the two messages
        self.spi.xfer2([address | (1 << 7), data & 0xFF])
        self.spi.xfer2([(address + 1) | (1 << 7), (data >> 8) & 0xFF])

    def read_from_register(self, address):
        """
        Read from the specified register and return the 16 bits of data.

        Parameters
        ----------
        address: int
            7 bit address of the register. This is the address of register containing the MSB

        Returns
        -------
        int
            16 bit number of the data returned
        """
        self.wait_for_sensor()

        # Send the address to read from, and make sure the write bit is set to 0
        self.spi.xfer2([address & ~(1 << 7), 0x00])

        rcv = self.spi.readbytes(2)
        return (rcv[0] << 8) | rcv[1]

    def read_fft_data(self):
        """
        Reads from sensor the FFT data and return as a list of FFTRecord
        """
        self.wait_for_sensor()

        # Data returned is an array, so combine both elements to get the real number
        combineData = lambda data: (data[0] << 8) | data[1]

        # Get the correct value from the data received. This will be in mg
        getValue = lambda data: (2 ** ((combineData(data) / 2048)) / FFTAverages) * 0.9535

        data = list()

        samplerate = 220000 / 2 ** AVG_CNT_Bit
        binsize = samplerate / 4096

        axis = [X_BUF, Y_BUF, Z_BUF]
        axis_data = [list(), list(), list()]

        self.spi.xfer2([axis[0] & ~(1 << 7), 0x00])
        for n, a in enumerate(axis):
            for i in range(2048):
                if i != 2047:
                    rcv = self.spi.xfer2([a & ~(1 << 7),
                                          0x00])  # Remember that any data requested will only arrive at the next spi transaction
                elif n < 2:
                    rcv = self.spi.xfer2([axis[n + 1] & ~(1 << 7), 0x00])  # Request right away for the next axis
                else:
                    rcv = self.spi.xfer2([0x00, 0x00])  # If we are at the very end, don't request anything

                axis_data[n].append(getValue(rcv))

        # Combine the data from all axis together
        for i in range(2048):
            data.append(FFTRecord(binsize * i, binsize, axis_data[0][i], axis_data[1][i], axis_data[2][i]))

        return data

    def run(self):
        super().setup_logging("vibration",
                              ["binsize (Hz)", "lowestfrequency (Hz)", "value x (mg)", "value y (mg)", "value z (mg)"])
        self.setup()
        while True:
            self.check_sensor_connection(True)
            self.check_for_errors()

            self.write_to_register(GLOB_CMD, 1 << 11)  # Start a measurement
            self.wait_for_sensor()

            data = self.read_fft_data()
            now = time.time() * 1000
            for i in data:
                self.sensorlogger.info([now, i.binsize, i.lowestfrequency, i.x_data, i.y_data, i.z_data])
