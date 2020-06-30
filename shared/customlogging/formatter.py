import csv
import io
import logging


class CSVFormatter(logging.Formatter):
    '''
    Formats logging messages in csv format
    '''

    def __init__(self):
        super().__init__()
        self.output = io.StringIO()
        self.writer = csv.writer(self.output)

    def format(self, record):
        self.writer.writerow(record.msg)
        data = self.output.getvalue()
        self.output.truncate(0)
        self.output.seek(0)
        return data.strip()
