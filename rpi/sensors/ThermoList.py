from rpi.sensors.Thermo_1wire import Thermo
from rpi.sensors.Sensor import SensorLogging
import glob
import os


class ThermoList(SensorLogging):
    def __init__(self):
        super().__init__("thermometer", ["id", "value"])
        
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')
    
        self.sensor_list = list()
        
        for i in device_folders:        
            t = Thermo(os.path.basename(i))
            self.sensor_list.append(t)
            
    def readAll(self):
        result = list() 
        for i in self.sensor_list:
            result.append(i.read())
        return result

    def loop(self):
        raise NotImplementedError
