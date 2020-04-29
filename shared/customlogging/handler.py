import logging
import os
from datetime import datetime


class MakeFileHandler(logging.FileHandler):
    '''
    Simple extension from logging.FileHandler that will not throw an error
    if the directory doesn't exist. In that case, it will just create it itself
    '''
    def __init__(self, location, foldername, subfolder=None, filetype='log', mode='a', encoding=None, delay=False):
        '''
        location: First folder inside logs. Should be either 'laptop' or 'rpi'
        foldername: Folder inside location.
        subfolder: Optional. If we need another folder level. Mainly used for sensor logging.
        '''
        if subfolder is None:
            fileName = datetime.now().strftime(f"{location}.{foldername}_%Y-%m-%d %H-%M-%S.{filetype}")
            path = f'logs/{location}/{foldername}/{fileName}'
        else:
            fileName = datetime.now().strftime(f"{location}.{subfolder}_%Y-%m-%d %H-%M-%S.{filetype}")
            path = f'logs/{location}/{foldername}/{subfolder}/{fileName}'

        os.makedirs(os.path.dirname(path), exist_ok=True)
        logging.FileHandler.__init__(self, path, mode, encoding, delay)