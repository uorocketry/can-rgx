"""
Code for interacting with the Teensy. The main use of this file is to provide a central way to access the Teensy and
avoid possible race conditions.
"""
import logging

import serial
import glob


class Teensy:
    def __init__(self):
        self.init_serial()

    def init_serial(self):
        ports = glob.glob('/dev/ttyACM[0-9]*')
        self.ser = serial.Serial(ports[0], 115200, timeout=1)

    def activate_motor(self, motor_number, motor_direction):
        try:
            data = ((motor_number & 1) << 1) | (motor_direction & 1)
            data |= 0b1001 << 2
            self.ser.write(str.encode(f"{data}\n"))
        except Exception as e:
            logging.getLogger(__name__).error("Could not write to Teensy. Trying to reset serial.")
            self.init_serial()
            raise e

    def get_motor_state(self):
        self.ser.flushInput()
        state = int(self.ser.readline().decode('utf-8').rstrip())
        return (state >> 7) & 0b1111

    def get_led_state(self):
        self.ser.flushInput()
        state = int(self.ser.readline().decode('utf-8').rstrip())
        return state & 0b1111111
