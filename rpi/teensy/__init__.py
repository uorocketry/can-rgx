"""
Code for interacting with the Teensy. The main use of this file is to provide a central way to access the Teensy and
avoid possible race conditions.
"""
import threading

from smbus import SMBus

TEENSY_ADDRESS = 0x8


# These value are sent to the Teensy to select what it will return on a read operation
class I2CReadState:
    MOTOR = 0b00
    LED = 0b01


class Teensy:
    # The reading operations are not atomic, i.e. it takes two i2c commands to read from the Teensy. Therefore, we
    # have this lock to prevent race conditions
    lock = threading.Lock()

    def __init__(self):
        self.bus = SMBus(1)

    def activate_motor(self, motor_number, motor_direction):
        self.bus.write_byte(TEENSY_ADDRESS, 0b100 | ((motor_number & 1) << 1) | motor_direction & 1)

    def get_motor_state(self):
        with Teensy.lock:
            self.bus.write_byte(TEENSY_ADDRESS, I2CReadState.MOTOR & 0b11)  # Tell the Teensy to return motor info
            return self.bus.read_byte(TEENSY_ADDRESS)

    def get_led_state(self):
        with Teensy.lock:
            self.bus.write_byte(TEENSY_ADDRESS, I2CReadState.LED & 0b11)  # Tell the Teensy to return led info
            return self.bus.read_byte(TEENSY_ADDRESS)
