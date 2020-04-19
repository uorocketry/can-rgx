import glob
import time
import logging

class Thermo:
    
    names = {'00000bc743d3':'1',
            '00000bcada29':'2'}

    def __init__(self, identity, sensorlogger):
        self.device_file = '/sys/bus/w1/devices/' + identity + '/w1_slave'
        self.sensorlogger = sensorlogger
        self.logger = logging.getLogger(__name__)

        if identity in Thermo.names:
            self.logger.debug("Thermometer {} has been added".format(identity))
            self.name = Thermo.names[identity]
        else:
            self.logger.warning("Thermometer with identity {} is not listed in known sensors".format(identity))
            self.name = 'UNDEFINED'

    def read_temp_raw(self):
        f = open(self.device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    #the read method called from the main class.
    def read(self):
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

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

