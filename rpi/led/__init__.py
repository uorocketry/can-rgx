import logging
import threading
import time

from DMXEnttecPro import Controller

from shared.customlogging.errormanager import ErrorManager


class LEDs:
    def __init__(self):
        try:
            # TODO: Use the proper identifier for the USB device
            self.dmx = Controller('/dev/ttyUSB0', auto_submit=True)
        except IOError:
            em = ErrorManager(__name__)
            # TODO: Maybe retry to connect after a timeout? Would need to use a separate thread.
            em.error("Could connect to the DMX controller! Please restart the RPi server.", "DMX_CONNECTION")

        # Use a lock to access the DMX Controller. Not clear if this is needed, but better be safe than worry.
        self.lock = threading.Lock()

    def __activate_led(self, led_number):
        with self.lock:
            logger = logging.getLogger(__name__)
            logger.info("Activating LED {}".format(led_number))
            self.dmx.set_channel(led_number, 50)  # TODO: Set the appropriate intensity value
            time.sleep(5)  # TODO: Check if the LEDs turned on using the Teensy
            self.dmx.set_channel(led_number, 0)
            logger.info("LED {} has finished activating".format(led_number))

    def activate_led(self, led_number):
        threading.Thread(target=self.__activate_led, args=([led_number])).start()
