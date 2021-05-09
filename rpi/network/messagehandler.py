import json
import logging
import logging.handlers

from rpi.motor import MotorControl, MotorDirection
from rpi.led import LEDs
from shared.network.requesttypes import RequestTypes


class MessageHandler:
    def __init__(self):
        self.motor_control = MotorControl()
        self.leds = LEDs()

    def process_message(self, json_string, client_adr):
        logger = logging.getLogger(__name__)

        try:
            data = json.loads(json_string)
        except json.JSONDecodeError:
            logger.error("Cannot decode JSON string")
            return

        if data['type'] == RequestTypes.PING:
            logger.debug("Received a ping from {}".format(client_adr[0]))
        elif data['type'] == RequestTypes.CONTROLMOTOR:
            self.motor_control.start_motor(data['motorNumber'], MotorDirection.DOWN)
        elif data['type'] == RequestTypes.CONTROLLED:
            self.leds.activate_led(data['ledNumber'])
        else:
            logger.error("Received an unknown message type")
