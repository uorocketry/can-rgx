#!/usr/bin/python3

# Fallback script that can be used in the event that the GUI is not able to activate the motors.

import logging
import time

from rpi.motor import MotorDirection
from rpi.teensy import Teensy

teensy = Teensy()
logger = logging.getLogger(__name__)

motor_number = input("Which motor should we activate (0 or 1)?")

if motor_number != 0 and motor_number != 1:
    logger.error("Input should be either 0 or 1")

logger.info("Starting motor {}".format(motor_number + 1))
teensy.activate_motor(motor_number, MotorDirection.DOWN)

status = 0b11
while (status >> 1) == 1:  # Wait here until the motor stops running
    time.sleep(1)

    if motor_number == 0:
        status = teensy.get_motor_state() >> 2
    else:
        status = teensy.get_motor_state()

logger.info("Motor {} stopped".format(motor_number + 1))

if status & 1 == 1:
    logger.error("Motor {} is in an error state! Did the limit switch break?".format(motor_number + 1))
else:
    logger.error(
        "Error for motor {} has been cleared. Please still proceed carefully.".format(motor_number + 1))
