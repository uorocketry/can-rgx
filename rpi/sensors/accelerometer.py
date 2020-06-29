import spidev
import time

#relevant registers
DATA_FORMAT =  0x31      #clear bit d6 for 4 wire, set for 3 wire
BW_RATE = 0x2C           #date and power mode control
POWER_CTL = 0x2D            #power saving features control 
    
DATA_X0 = 0x32     #x-axis data0
DATA_X1 = 0x33     #x-axis data1
DATA_Y0 = 0x34     #y-axis data0
DATA_Y1 = 0x35     #y-axis data1
DATA_Z0 = 0x36     #z-axis data0
DATA_Z1 = 0x37     #z-axis data1

# SPI config
SPI_MAX_CLOCK_HZ = 125000000 #125MHz
SPI_MODE = 0b01   #or 0b01
SPIBus = 0
SPIDevice = 1     #0 or 1

# Data Range
RANGE_2G = 0b00000100  #10bit resolution , +/- 2g
RANGE_4G = 0b00001101
RANGE_8G = 0b00001110
RANGE_16G = 0b00001111

#Other macros
READ_BIT = 0x01
WRITE_BIT = 0x00
DUMMY_BYTE = 0x00
MEASURE_MODE = 0b00001000 
OUTPUT_RATE = 0b00001111

class Accelerometer:
    def __init__(self, measure_range=RANGE_2G):
        # SPI init
        self.spi = spidev.SpiDev()
        self.spi.open(SPIBus, SPIDevice)
        self.spi.max_speed_hz = SPI_MAX_CLOCK_HZ
        self.spi.mode = SPI_MODE

        # Device init
        self._set_measure_range(measure_range)
        self._enable_measure_mode()
        self._set_bw_rate()


    def write_data(self, address, value):
        """Writes data in device address.
        Args:
            address (int): Address to write in.
            value (int): Value to write in address.
        Returns:
            None
        """
        device_address = address << 1 | WRITE_BIT    #sets LSB to 0
        self.spi.xfer2([device_address, value])
        print("written.\n")

    def read_data(self, address):
        """Reads data from device.
        Args:
            address (int): Address to read from.
        Returns:
            int: Value in speficied address.
        """
        device_address = address << 1 | READ_BIT
        self.spi.xfer2([device_address, DUMMY_BYTE])[1]
        ret = self.spi.readbytes(1)
        return ret

    def read_multiple_data(self, address_list):
        """Reads multiple data from device.
        Args:
            address_list (list): List of addresses to read from.
        Returns:
            list: Value of each address.
        """
        cat_add = []   #list address instrucs
        for address in address_list:
            cat_add.append(address << 1 | READ_BIT)
        cat_add.append(DUMMY_BYTE)

        self.spi.xfer2(cat_add)[1:]
        
        #this line doesn't seem to be working, data is updated in cat_add
        #read_data = self.spi.readbytes(6)

        return cat_add


    def _set_measure_range(self, measure_range):
        """Sets measure range on device.
        Args:
            measure_range (int): Measure range to set in ADXL355.
        Returns:
            None
        """
        print ("Set measure range...")
        self.write_data(DATA_FORMAT, measure_range)

    def _enable_measure_mode(self):
        """
        Enables measure mode.
        Returns:
            None
        """
        self.write_data(POWER_CTL, MEASURE_MODE)

    def _set_bw_rate(self):
        """
        Sets output data rate (3200Hz)
        Returns:
            None
        """
        self.write_data(BW_RATE, OUTPUT_RATE)


    def get_axes(self):
        """
        Gets the current data from the axes.
        Returns:
            dict: Current value for x, y and z axis
        """

        # Reading data
        raw_data = self.read_multiple_data(
            [DATA_X0, DATA_X1, DATA_Y0, DATA_Y1, DATA_Z0, DATA_Z1]
        )

        x_data = raw_data[0:2]
        print(x_data)
        y_data = raw_data[2:4]
        print(y_data)
        z_data = raw_data[4:6]
        print(z_data)


        # Combine data
        x_data = (x_data[0] >> 4) + (x_data[1] << 4) 
        y_data = (y_data[0] >> 4) + (y_data[1] << 4) 
        z_data = (z_data[0] >> 4) + (z_data[1] << 4) 

        # Apply 2s comp
        if x_data & 0x80000 == 0x80000:
            x_data = ~x_data + 1

        if y_data & 0x80000 == 0x80000:
            y_data = ~y_data + 1

        if z_data & 0x80000 == 0x80000:
            z_data = ~z_data + 1



        # Return values
        retval = [x_data, y_data, z_data]
        return (retval)

        #Convert to readable values



def main():
    adxl = Accelerometer()
    while True:
      val = adxl.get_axes()
      print(val)
      time.sleep(5)

if __name__ == "__main__": 
    main()