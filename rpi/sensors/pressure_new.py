import struct
import time
import spidev
from rpi.sensors.sensorlogging import SensorLogging
from shared.customlogging.errormanager import ErrorManager

#Registers Index
PADC_MSB = 0X00    #10-bit pressure ADC output value MSB
PADC_LSB = 0X01    # " LSB
TADC_MSB = 0X02    #10-bit temperature ADC output value MSB
TADC_LSB = 0X03    # " LSB

A0MSB = 0x04    #A0 coefficient MSB
AOLSB = 0x05    #A0 coefficient LSB
B1MSB = 0x06
B1LSB = 0x07
B2MSB = 0x08
B2LSB = 0x09
C12MSB = 0x0A
C12LSB = 0x0B
CONVERT_REG = 0x12  #Start pressure and temp. conversion

#SPI Config
SPI_MAX_CLOCK_HZ = 300000   #300kHz
SPI_MODE = 0b11
SPIBus = 0
SPIDevice = 0
CSHIGH = False  #CS Low on start of transmission

#Register Values

class Pressure(SensorLogging):
    def setup(self):
        self.spi = spidev.SpiDev()
        self.spi.open(SPIBus, SPIDevice)
        self.spi.max_speed_hz = SPI_MAX_CLOCK_HZ
        self.spi.mode = SPI_MODE

        self.check_sensor_connection()

    def check_sensor_connection(self):
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