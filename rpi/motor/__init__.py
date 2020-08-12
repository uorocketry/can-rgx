import logging
import threading
import time
from enum import IntEnum

from smbus import SMBus

ARDUINO_ADDRESS = 2


class MotorDirection(IntEnum):
    UP = 0
    DOWN = 1


class MotorControl:
    def __init__(self):
        self.bus = SMBus(1)

    def __start_motor(self, motor_number, motor_direction):
        logger = logging.getLogger(__name__)
        logger.info("Starting motor {}".format(motor_number + 1))
        self.bus.write_byte(ARDUINO_ADDRESS, (motor_number << 1) | motor_direction)

        status = 0b11
        while (status >> 1) == 1:  # Wait here until the motor stops running
            time.sleep(1)

            if motor_number == 0:
                status = self.bus.read_byte(ARDUINO_ADDRESS) >> 2
            else:
                status = self.bus.read_byte(ARDUINO_ADDRESS)

        logger.info("Motor {} stopped".format(motor_number + 1))

        if status & 1 == 1:
            # TODO: Use the Error Manager
            logger.error("Motor {} is in an error state! Did the limit switch break?".format(motor_number + 1))

    def start_motor(self, motor_number, motor_direction):
        threading.Thread(target=self.__start_motor, args=(motor_number, motor_direction)).start()
