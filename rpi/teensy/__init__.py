"""
Code for interacting with the Teensy. The main use of this file is to provide a central way to access the Teensy and
avoid possible race conditions.
"""
import serial


class Teensy:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

    def activate_motor(self, motor_number, motor_direction):
        data = ((motor_number & 1) << 1) | (motor_direction & 1)
        data |= 0b1001 << 2
        self.ser.write(str.encode(f"{data}\n"))

    def get_motor_state(self):
        self.ser.flushInput()
        state = int(self.ser.readline().decode('utf-8').rstrip())
        return (state >> 7) & 0b1111

    def get_led_state(self):
        self.ser.flushInput()
        state = int(self.ser.readline().decode('utf-8').rstrip())
        return state & 0b1111111
