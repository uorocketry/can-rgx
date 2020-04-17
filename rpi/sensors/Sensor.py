import os
import csv
from abc import ABC, abstractmethod

class BaseSensor(ABC):
    def __init__(self, filename, dataRow):
        '''
        Parameters:
            filename : name of the file to use
            dataRow : list representing the header of the csv file
        '''

        self.filename = filename
        self.dataRow = dataRow


    def writeDataToFile(self, data):
        file = None
        
        try:
            if not os.path.exists(self.filename):
                self.initFile()
            file = open(self.filename, "a")
                
        except IOError:
            print("Error opening file!")
            return
            
        writer = csv.writer(file)
        writer.writerow(data)
        
        file.close()


    def initFile(self):
        with open(self.filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.dataRow)

    @abstractmethod
    def loop(self):
        pass