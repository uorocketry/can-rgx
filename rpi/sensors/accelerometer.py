import time
import spidev

class Accelerometer():
    # registers index
    DATA_FORMAT = 0x31  # clear bit d6 for 4 wire, set for 3 wire
    BW_RATE = 0x2C  # date and power mode control
    POWER_CTL = 0x2D  # power saving features control
    FIFO_CTL = 0x38  # FIFO mode select

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
    RANGE_2G = 0b00001100  # full resolution (10bits) , left-justified MSB mode, +/- 2g
    RANGE_4G = 0b00001101  # full resolution (11bits), MSB mode, +/- 4g
    RANGE_8G = 0b00001110  # full resolution(12bits), MSB mode, +/-8g
    RANGE_16G = 0b00001111  # full resolution(13bits), MSB mode, +/-16g
    # self test:
    SELF_TEST = 0b10001111  # full resolution (13bits) MSB mode, +/-16g

    # register values
    MEASURE_MODE = 0b00001000  # set device to measure mode (D3)
    BW_OUTPUT_RATE = 0b00001111  # normal operation, 3200Hz output rate, 1600Hz bandwidth
    FIFO_MODE = 0b10011111  # stream mode, INT1 triggered, 31bit buffer
    FIFO_BYPASS = 0b00000000
    READ_BIT = 0x01
    WRITE_BIT = 0x00
    DUMMY_BYTE = 0x00
    SEQUENTIAL_READ_BYTE = 0b11

    # Conversion factors
    CONV_FULLR = 3.9  # applicable for all gs
    CONV_2G_10B = 3.9  # mg/LSB
    CONV_4G_10B = 7.8
    CONV_8G_10B = 15.6
    CONV_16G_10B = 31.2

    def __init__(self, measure_range=RANGE_4G):
        self.spi = spidev.SpiDev()
        self.spi.open(self.SPIBus, self.SPIDevice)
        self.spi.max_speed_hz = self.SPI_MAX_CLOCK_HZ
        self.spi.mode = self.SPI_MODE

        self.get_device_id()
        self.set_measure_range(measure_range)
        self.set_fifo()
        self.set_bw_rate()
        self.enable_measure_mode()

    def get_device_id(self):
        dev_id = self.xfer_read_byte(0x00, 1)
        address_list = [0x00, 0x1D, 0x1E]
        multibyte_test = self.xfer_read_multiple_bytes_sequential(start_address=0x00, n=3)
        print(f"Device ID : {dev_id}")
        print(f"mutlibyte read test : {multibyte_test}")

    def set_measure_range(self, measure_range):
        """Function to set range and resolution"""
        self.xfer_write_byte(self.DATA_FORMAT, measure_range)

    def set_fifo(self):
        """Function to set FIFO mode"""
        self.xfer_write_byte(self.FIFO_CTL, self.FIFO_MODE)

    def set_bw_rate(self):
        """Function to set bandwidth and output data rate"""
        self.xfer_write_byte(self.BW_RATE, self.BW_OUTPUT_RATE)

    def enable_measure_mode(self):
        """Function to activate ADLX343 and initiate measurement"""
        self.xfer_write_byte(self.POWER_CTL, self.MEASURE_MODE)

    def xfer_write_byte(self, address, value):
        """SPI function to write bytes, set MSB low"""
        self.spi.xfer2([(address | self.WRITE_BIT << 7), value & 0XFF])

    def xfer_read_byte(self, address, n):
        """"FIX THIS  'list' and 'int' error SPI function to read bytes, set MSB high to read"""
        retval = self.spi.xfer2([(address | self.READ_BIT << 7), 0x00])[1:]
        return retval

    def xfer_read_multiple_bytes(self, data_address_list):
        spi_read = []
        for address in data_address_list:
            spi_read.append(address | self.READ_BIT << 7)
        spi_read.append(self.DUMMY_BYTE)
        retlist = self.spi.xfer2(spi_read)[1:]
        #retlist = self.spi.readbytes(12)
        return retlist

    def xfer_read_multiple_bytes_sequential(self, start_address, n):
        spi_read = [start_address | (self.SEQUENTIAL_READ_BYTE << 6)]
        for _ in range(n):
            spi_read.append(self.DUMMY_BYTE)
        retlist = self.spi.xfer2(spi_read)[1:]
        # retlist = self.spi.readbytes(12)
        return retlist

    def get_acceleration_data(self):
        data_address_list = [self.DATA_X0, self.DATA_X1, self.DATA_Y0, self.DATA_Y1, self.DATA_Z0, self.DATA_Z1]
        raw_axes = self.xfer_read_multiple_bytes_sequential(start_address=self.DATA_X0, n=6)
        print(raw_axes)

        x_data = raw_axes[0:2]
        y_data = raw_axes[2:4]
        z_data = raw_axes[4:6]


        #Combine data
        x_data = (x_data[1] << 8) | x_data[0]
        x_data >> 4     #right-shift to discard lower 4 bits
        y_data = (y_data[1] << 8) | y_data[0]
        y_data >> 4
        z_data = (z_data[1] << 8) | z_data[0]
        z_data >> 4

        # Apply 2s comp
        if x_data & 0x80000 == 0x80000:
            x_data = ~x_data + 1

        if y_data & 0x80000 == 0x80000:
            y_data = ~y_data + 1

        if z_data & 0x80000 == 0x80000:
            z_data = ~z_data + 1

        ret = [x_data, y_data, z_data]

        #Convert from LSB/mg to mg
        for i in range(len(ret)):
            ret[i] = (ret[i]*self.CONV_FULLR)

        # Return values
        print (ret)




def main():
    while True:
        adxl = Accelerometer()
        val = adxl.get_acceleration_data()
        print(val)
        time.sleep(1)


if __name__ == "__main__":
    main()








