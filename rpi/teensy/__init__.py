"""
Code for interacting with the Teensy. The main use of this file is to provide a central way to access the Teensy and
avoid possible race conditions.
"""
import logging

import serial
import glob

from tenacity import retry, stop_after_attempt


class Teensy:
    def __init__(self):
        ports = glob.glob('/dev/ttyACM[0-9]*')
        self.ser = serial.Serial(ports[0], 115200, timeout=1)
        self.current_port = ports[0]

    def check_serial(self):
        """
        Workaround for unreliable USB cable sometime reconnecting, changing the serial port
        """
        ports = glob.glob('/dev/ttyACM[0-9]*')
        if ports[0] != self.current_port:
            logging.getLogger(__name__).warning("Teensy seems to have changed port. Updating accordingly...")
            self.ser = serial.Serial(ports[0], 115200, timeout=1)
            self.current_port = ports[0]

    def activate_motor(self, motor_number, motor_direction):
        self.check_serial()
        data = ((motor_number & 1) << 1) | (motor_direction & 1)
        data |= 0b1001 << 2
        self.ser.write(str.encode(f"{data}\n"))

    @retry(stop=stop_after_attempt(5))
    def get_motor_state(self):
        self.check_serial()
        self.ser.flushInput()
        state = int(self.ser.readline().decode('utf-8').rstrip())
        return (state >> 7) & 0b1111

    @retry(stop=stop_after_attempt(5))
    def get_led_state(self):
        self.check_serial()
        self.ser.flushInput()
        state = int(self.ser.readline().decode('utf-8').rstrip())
        return state & 0b1111111
