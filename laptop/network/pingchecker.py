import threading
import logging
import time

from laptop.network.client import send_message
from shared.network.requesttypes import RequestTypes

class PingChecker(threading.Thread):
    '''
    Continuously sends pings to the RPI. If the RPI cannot be reached
    for some reasons, alert the user. The goal is to catch network problems
    as soon as possible.
    '''
    def __init__(self):
        super().__init__()

        self.setDaemon(True)

    def run(self):
        logger = logging.getLogger(__name__)

        inError = False
        tryCount = 10
        message = {'type': RequestTypes.PING}
        while True:
            confirm = send_message(message)

            if confirm and inError:
                logger.info("Ping sent successfully to RPI", extra={'errorID': 'RPIPing'})
                inError = False
                tryCount = 10
            elif not confirm:
                inError = True
                if tryCount >= 5: #Try not to spam the user if there is an error
                    logger.warning("Error while sending ping to RPI", extra={'errorID': 'RPIPing'})
                    tryCount = -1
                
                tryCount += 1

            
            if not inError:
                time.sleep(10)
            else:
                time.sleep(1)
