import logging
import threading
import time

from DMXEnttecPro import Controller
from DMXEnttecPro.utils import get_port_by_serial_number

from rpi.teensy import Teensy
from shared.customlogging.errormanager import ErrorManager


class LEDs:
    def __init__(self):
        try:
            port = get_port_by_serial_number('6A011004')
            self.dmx = Controller(port, auto_submit=True)
        except IOError:
            em = ErrorManager(__name__)
            # TODO: Maybe retry to connect after a timeout? Would need to use a separate thread.
            em.error("Could connect to the DMX controller! Please restart the RPi server.", "DMX_CONNECTION")

        # Use a lock to access the DMX Controller. Not clear if this is needed, but better be safe than worry.
        self.lock = threading.Lock()
        self.teensy = Teensy()
        self.em = ErrorManager(__name__)

    def __activate_led(self, led_number):
        with self.lock:
            logger = logging.getLogger(__name__)
            logger.info("Activating LED {}".format(led_number))
            self.dmx.set_channel(led_number, 50)  # TODO: Set the appropriate intensity value
            time.sleep(5)

            # Use the photodiode to verify if the LED turned on
            try:
                led_state = self.teensy.get_led_state()
                logger.debug("LED State: {}".format(led_state + 1))
                if (led_state << led_number) & 0b1 == 1:
                    self.em.resolve("Successfully verified LED {} turned on".format(led_number), led_number)
                else:
                    self.em.error("LED {} did not turn on".format(led_number), led_number)

                # Resolve the error if we threw earlier
                self.em.resolve("Could not retrieve LED state from the Teensy", f"teensy_{led_number}", False)
            except Exception as e:
                self.em.error("Could not check LED State from the Teensy: {}".format(e), f"teensy_{led_number}")

            self.dmx.set_channel(led_number, 0)
            logger.info("LED {} is off".format(led_number))

    def activate_led(self, led_number):
        threading.Thread(target=self.__activate_led, args=([led_number])).start()
