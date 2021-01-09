import threading
import time

from laptop.network.client import send_message
from shared.customlogging.errormanager import ErrorManager
from shared.network.requesttypes import RequestTypes


class PingChecker(threading.Thread):
    """
    Continuously sends pings to the RPI. If the RPI cannot be reached
    for some reasons, alert the user. The goal is to catch network problems
    as soon as possible.
    """

    def __init__(self):
        super().__init__()

        self.setDaemon(True)

    def run(self):
        message = {'type': RequestTypes.PING}
        error_manager = ErrorManager(10)
        while True:
            confirm = send_message(message)

            if not confirm:
                inError = True
                error_manager.warning("Error while sending ping to RPI", "RPIPing")
            else:
                inError = False
                error_manager.resolve("Ping sent successfully to RPI", "RPIPing", False)

            if not inError:
                time.sleep(10)
            else:
                time.sleep(1)
