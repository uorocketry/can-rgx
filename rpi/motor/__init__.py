import logging
import threading
import time

from rpi.teensy import Teensy
from shared.customlogging.errormanager import ErrorManager


class MotorControl:
    def __init__(self):
        self.teensy = Teensy()
        self.em = ErrorManager(__name__)

    def __start_motor(self, motor_number, motor_direction):
        logger = logging.getLogger(__name__)
        logger.debug("Starting motor {}".format(motor_number + 1))
        try:
            self.teensy.activate_motor(motor_number, motor_direction)
            self.em.resolve("Started motor {}".format(motor_number + 1), f"motor_{motor_number}_start")
        except:
            self.em.error("Could not send start motor {} command to Teensy".format(motor_number + 1),
                          f"motor_{motor_number}_start")

        try:
            status = 0b11
            while (status >> 1) == 1:  # Wait here until the motor stops running
                time.sleep(1)

                if motor_number == 0:
                    status = self.teensy.get_motor_state() >> 2
                else:
                    status = self.teensy.get_motor_state()

            logger.info("Motor {} stopped".format(motor_number + 1))

            if status & 1 == 1:
                self.em.error("Motor {} is in an error state! Did the limit switch break?".format(motor_number + 1),
                              motor_number)
            else:
                self.em.resolve(
                    "Error for motor {} has been cleared. Please still proceed carefully.".format(motor_number + 1),
                    motor_number, False)

            self.em.resolve("Motor state from the Teensy can now be received", f"motor_state", False)
        except:
            self.em.error("Could not retrieve motor state from the Teensy", f"motor_state")

    def start_motor(self, motor_number, motor_direction):
        threading.Thread(target=self.__start_motor, args=(motor_number, motor_direction)).start()
