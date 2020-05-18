import logging
import spidev

from rpi.sensors.sensorlogging import SensorLogging

#Only bus 0 is available on RPi
SPIBus = 0
#Chip select. Either 0 or 1
SPIDevice = 0


class Vibration(SensorLogging):
    '''
    Class which interacts with an ADcmXL3021 vibration sensor.
    '''

    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(SPIBus, SPIDevice)

        #Configure the settings to communicate with the device
        self.spi.mode = 0b11
        self.spi.max_speed_hz = 14000000 #14MHz
        self.spi.lsbfirst = False
        
    
    def __del__(self):
        self.spi.close()

    def write_to_register(self, address, data):
        '''
        Write to the specified 16 bit wide register.

        Parameters
        ----------
        address: int
            7 bit address of the register. This is the address of register containing the MSB
        data: int
            16 bit of data to write
        '''
        #Send message in two parts, each containing 16 bits.
        #First bit is 1 for the write bit, followed by the 7 bit address
        #This is followed by the data, which has been splited accross the two messages
        self.spi.xfer2([address | (1 << 7), data & 0xFF])
        self.spi.xfer2([(address+1) | (1 << 7), (data >> 8) & 0xFF])

    def read_from_register(self, address):
        '''
        Read from the specified register and return the 16 bits of data.

        Parameters
        ----------
        address: int
            7 bit address of the register. This is the address of register containing the MSB
        
        Returns
        -------
        int
            16 bit number of the data returned
        '''
        #Send the address to read from, and make sure the write bit is set to 0
        self.spi.xfer2([address & ~(1 << 7), 0x00])

        rcv = self.spi.readbytes(2)
        return (rcv[0] << 8) | rcv[1]

    def logging_loop(self):
        pass