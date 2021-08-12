import struct
import time
import smbus
from rpi.sensors.sensorlogging import SensorLogging
from shared.customlogging.errormanager import ErrorManager

PRES_SENS_ADDRESS = 0x76 #SDO to GND

#Registers Index
CMD = 0x7E
CONFIG = 0x1F       #sets IIR filter coeff
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


#Register Values
POWER_MODE = 0b00001111     #Enable pressure and temp. measurement, normal mode
ODR_MODE = 0x02             #Output data rate 50Hz - Recommended Drone setting
OSR_MODE_HIGHRES = 0b00000101   #Oversampling rate (highest resolution) 21bit / 0.085 Pa
IF_CONF_MODE = 0b00000000   #4-wire mode, watchdog timer disabled

#Recommended Drone setting:
OSR_MODE_STANRES = 0b00000010   #Oversampling rate (standard resolution) 18bit / 0.66 Pa; x4 oversampling for Pressure, none Temp
IIR_CONFIG_MODE = 0b00000010    #Filter coefficient 3

#Compensation Coeff Register Addresses
NVM_PAR_P11 = 0x45
NVM_PAR_P10 = 0x44
NVM_PAR_P9_H = 0x43
NVM_PAR_P9_L = 0x42
NVM_PAR_P8 = 0x41
NVM_PAR_P7 = 0x40
NVM_PAR_P6_H = 0x3F
NVM_PAR_P6_L = 0x3E
NVM_PAR_P5_H = 0x3D
NVM_PAR_P5_L = 0x3C
NVM_PAR_P4 = 0x3B
NVM_PAR_P3 = 0x3A
NVM_PAR_P2_H = 0x39
NVM_PAR_P2_L = 0x38
NVM_PAR_P1_H = 0x37
NVM_PAR_P1_L = 0x36

NVM_PAR_T3 = 0x35
NVM_PAR_T2_H = 0x34
NVM_PAR_T2_L = 0x33
NVM_PAR_T1_H = 0x32
NVM_PAR_T1_L = 0x31



class Pressure(SensorLogging):
    def setup(self):
        self.bus = smbus.SMBus(1)
        self.set_power_mode()
        self.check_sensor_connection()
        self.set_output_data_rate()
        self.set_oversampling_rate()
        #uncomment next line to use IIR filter (output approx. 3.2Pa noise with filter disabled; 1.2Pa enabled)
        #self.set_IIR_filter_coef()
        self.set_serial_interface()
        self.get_compensation_coefficients()


    def check_sensor_connection(self):
        """
        Checks if the correct sensor is connected, or if anything is connected
        at all. If the sensor is not connected, an error will be logged and this
        function will block until it connects.
        """
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

    def set_oversampling_rate(self):
        """Method to set oversampling rate"""
        self.bus.write_byte_data(PRES_SENS_ADDRESS, OSR, OSR_MODE_STANRES)

    def set_IIR_filter_coef(self):
        """Method to set IIR filter coefficient for noise reduction"""
        self.bus.write_byte_data(PRES_SENS_ADDRESS, CONFIG, IIR_CONFIG_MODE)

    def set_serial_interface(self):
        """Method to set serial interface settings."""
        self.bus.write_byte_data(PRES_SENS_ADDRESS, IF_CONF, IF_CONF_MODE)

    def get_compensation_coefficients(self):
        """Method to read and save compensation coeff to be used for converting raw to physical output"""
        #8-bit pressure coeff:
        self.P11 = (self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P11)) / (2**65.0)
        self.P10 = (self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P10)) / (2**48.0)
        self.P8 = (self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P8)) / (2**15.0)
        self.P7 = (self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P7)) / (2**8.0)
        self.P4 = (self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P4)) / (2**37.0)
        self.P3 = (self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P3)) / (2**32.0)

        #16-bit pressure coeff:
        P9_high = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P9_H)
        P9_low = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P9_L)
        self.P9 = (P9_high << 8 | P9_low) / (2 ** 48.0)

        P6_high = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P6_H)
        P6_low = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P6_L)
        self.P6 = (P6_high << 8 | P6_low) / (2 ** 6.0)

        P5_high = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P5_H)
        P5_low = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P5_L)
        self.P5 = (P5_high << 8 | P5_low) / (2 ** (-3.0))

        P2_high = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P2_H)
        P2_low = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P2_L)
        P2 = P2_high << 8 | P2_low
        self.P2 = (P2 - (2**14.0))/(2**29.0)

        P1_high = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P1_H)
        P1_low = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_P1_L)
        P1 = P1_high << 8 | P1_low
        self.P1 = (P1 - (2**14.0))/(2**20.0)

        #8-bit temp coeff
        self.T3 = (self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_T3)) / (2**48.0)

        #16-bit temp coeff:
        T2_high = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_T2_H)
        T2_low = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_T2_L)
        self.T2 = (T2_high << 8 | T2_low) / (2 ** 30.0)

        T1_high = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_T1_H)
        T1_low = self.bus.read_byte_data(PRES_SENS_ADDRESS, NVM_PAR_T1_L)
        self.T1 = (T1_high << 8 | T1_low) / 2 ** (-8.0)


    def read_pressure(self):
        #Raw pressure values
        data0_pressure = self.bus.read_byte_data(PRES_SENS_ADDRESS, DATA0)
        data1_pressure = self.bus.read_byte_data(PRES_SENS_ADDRESS, DATA1)
        data2_pressure = self.bus.read_byte_data(PRES_SENS_ADDRESS, DATA2)

        #Raw temperature values
        data0_temp = self.bus.read_byte_data(PRES_SENS_ADDRESS, DATA3_T)
        data1_temp = self.bus.read_byte_data(PRES_SENS_ADDRESS, DATA4_T)
        data2_temp = self.bus.read_byte_data(PRES_SENS_ADDRESS, DATA5_T)

        #Parse sensor data - unsigned 24 bit format
        uncomp_pressure = data2_pressure << 16 | data1_pressure << 8 | data0_pressure
        uncomp_temp = data2_temp << 16 | data1_temp << 8 | data0_temp

        #temp compensation
        pd1 = uncomp_temp - self.T1
        pd2 = pd1 * self.T2
        temperature = pd2 + (pd1 * pd1) * self.T3

        #Pressure compensation
        pd1 = self.P6 * temperature
        pd2 = self.P7 * temperature ** 2.0
        pd3 = self.P8 * temperature ** 3.0
        po1 = self.P5 + pd1 + pd2 + pd3

        pd1 = self.P2 * temperature
        pd2 = self.P3 * temperature ** 2.0
        pd3 = self.P4 * temperature ** 3.0
        po2 = uncomp_pressure * (self.P1 + pd1 + pd2 + pd3)

        pd1 = uncomp_pressure ** 2.0
        pd2 = self.P9 + self.P10 * temperature
        pd3 = pd1 * pd2
        pd4 = pd3 + self.P11 * uncomp_pressure ** 3.0
        pressure = po1 + po2 + pd4

        return pressure


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