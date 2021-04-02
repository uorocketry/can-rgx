#!/usr/bin/python3

# Fallback script that can be used in the event that the GUI is not able to activate the LEDs.

import logging
import time

from DMXEnttecPro import Controller

led_number = input("Which LED should we turn on (0-7)?")  # TODO: Give the range for the LEDs

dmx = Controller('/dev/ttyUSB0', auto_submit=True)  # TODO: Use the proper identifier for the USB device

logger = logging.getLogger(__name__)
logger.info("Activating LED {}".format(led_number))
dmx.set_channel(led_number, 50)  # TODO: Set the appropriate intensity value
time.sleep(5)  # TODO: Check if the LEDs turned on using the Teensy
dmx.set_channel(led_number, 0)
logger.info("LED {} has finished activating".format(led_number))
