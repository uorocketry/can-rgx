import logging
import os


class MakeFileHandler(logging.FileHandler):
    '''
    Simple extension from logging.FileHandler that will not throw an error
    if the directory doesn't exist. In that case, it will just create it itself
    '''
    def __init__(self, filename, mode='a', encoding=None, delay=False):            
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)