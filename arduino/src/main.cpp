#include <Arduino.h>
#include <Wire.h>
#include "main.h"
#include "debug.h"
#include "motor.h"

// Ports for the motors. These uses the standard Arduino pin numbers
const uint8_t MOTOR1_EN = 5;
const uint8_t MOTOR1_IN1 = 6;
const uint8_t MOTOR1_IN2 = 7;
const uint8_t MOTOR2_EN = 8;
const uint8_t MOTOR2_IN1 = 9;
const uint8_t MOTOR2_IN2 = 10;

// Communication settings
const uint8_t I2C_ADDRESS = 0x2;
const uint64_t SERIAL_RATE = 9600;

Motor motor1(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2);
Motor motor2(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2);

void setup() {
    // Setup the Arduino as an i2c slave
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveI2CEvent);

#ifdef DEBUG
    Serial.begin(SERIAL_RATE);
#endif
}

void receiveI2CEvent(int) {
    while (Wire.available()) {
        uint8_t data = Wire.read();

        uint8_t motorNumber = (data >> 1) & 1;
        auto motorDirection = static_cast<MotorDirection>(data & 1);

        if (motorNumber == 0) {
            PRINT("Activating motor 1 in direction ");
            PRINTLN(motorDirection);

            motor1.startMotor(motorDirection);
        } else {
            PRINT("Activating motor 2 in direction ");
            PRINTLN(motorDirection);

            motor2.startMotor(motorDirection);
        }
    }
}

void loop() {
}