import glob
import time

class Thermo:
    
    names = {'00000bc743d3':'1',
            '00000bcada29':'2'}

    def __init__(self, identity):
        self.device_file = '/sys/bus/w1/devices/' + identity + '/w1_slave'
        
        if identity in Thermo.names:
            self.name = Thermo.names[identity]
        else:
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
            #time.sleep(0.2)
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

