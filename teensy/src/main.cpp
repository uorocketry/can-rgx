#include <Arduino.h>
#include <Wire.h>
#include "main.h"
#include "debug.h"
#include "motor.h"

// Ports for the motors.
const uint8_t MOTOR1_EN = 5;
const uint8_t MOTOR1_IN1 = 4;
const uint8_t MOTOR1_IN2 = 6;
const uint8_t MOTOR2_EN = 10;
const uint8_t MOTOR2_IN1 = 11;
const uint8_t MOTOR2_IN2 = 12;

// Limit switches for the motors
const uint8_t MOTOR1_TOP_LIMIT = 0;
const uint8_t MOTOR1_LOWER_LIMIT = 0;
const uint8_t MOTOR2_TOP_LIMIT = 0;
const uint8_t MOTOR2_LOWER_LIMIT = 0;

// Ports for the photodiodes. On a I2C read, the data will be sent in the listed order.
const uint8_t PHOTODIODE_PORTS[] = {
       22, //MSB
       12,
       20,
       17,
       16,
       15,
       14  //LSB
};

// Threshold at which the photodiodes should be recognized as HIGH.
const int PHOTODIODE_TRESHOLD = 50;

// Communication settings
const uint8_t I2C_ADDRESS = 0x2;
const uint64_t SERIAL_RATE = 9600;

// How long to wait in milliseconds before stopping a motor automatically
const volatile uint16_t MOTOR_TIMEOUT_MILLI = 10 * 1000;

// Store what we should send to the Pi for the i2C value
I2CSendingValue i2CSendingValue = I2CSendingValue::MOTOR;

Motor motor1(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2);
Motor motor2(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2);

void setup() {
    // Setup the Teensy as an i2c slave
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveI2CEvent);
    Wire.onRequest(sendI2CState);

    // Enable the internal pulldown resistors for the photodiodes
    for (auto i : PHOTODIODE_PORTS) {
        pinMode(i, INPUT_PULLDOWN);
    }

#ifdef DEBUG
    Serial.begin(SERIAL_RATE);
#endif
}

/**
 * This function expects to receive three bits from I2C.
 * If the 1st bit (MSB) is 1, the action will be a motor control.
 *  2nd bit: Represents the motorNumber (0 for motor 1 and 1 for motor 2)
 *  3rd bit: Represents the motor direction. 0 is UP, 1 is DOWN.
 * If the 1st bit is 0, it will simply change the sent output during a I2C read.
 *  2nd bit: Ignored.
 *  3rd bit: 0 will send motor state. 1 will send LED state
 */
void receiveI2CEvent(int) {
    while (Wire.available()) {
        uint8_t data = Wire.read();

        if ((data >> 2) & 1) { // This is a motor control event
            uint8_t motorNumber = (data >> 1) & 1;
            auto motorDirection = static_cast<MotorDirection>(data & 1);

            if (motorNumber == 0) {
                // Only start the motor if the limit is not pressed
                if (!(motorDirection == MotorDirection::UP && digitalRead(MOTOR1_TOP_LIMIT) == LOW) &&
                    !(motorDirection == MotorDirection::DOWN && digitalRead(MOTOR1_LOWER_LIMIT) == LOW)) {
                    motor1.startMotor(motorDirection);
                }
            } else {
                // Only start the motor if the limit is not pressed
                if (!(motorDirection == MotorDirection::UP && digitalRead(MOTOR2_TOP_LIMIT) == LOW) &&
                    !(motorDirection == MotorDirection::DOWN && digitalRead(MOTOR2_LOWER_LIMIT) == LOW)) {
                    motor2.startMotor(motorDirection);
                }
            }
        } else { // Change what a i2c read will send
            i2CSendingValue = static_cast<I2CSendingValue>(data & 1);
        }
    }
}

// Sends the motors state to the RPi in a 4 bit number, 2 bit for each motor.
// The MSB of a motor is set to 1 if that motor is moving. The LSB is set to 1 if that motor is in an error state.
// The two most significant bits are for motor 1, the other two LSB are for motor 2.
// For example, if motor 1 is not moving and in an error state, and motor 2 is moving and not in error state, 0110 will be sent
void sendI2CState() {
    uint8_t state = 0;
    if (i2CSendingValue == I2CSendingValue::MOTOR) {
        state = (motor1.isMoving() << 3) | (motor1.isInErrorState() << 2) | (motor2.isMoving() << 1) |
                motor2.isInErrorState();
    } else if (i2CSendingValue == I2CSendingValue::LED) {
        for (auto i : PHOTODIODE_PORTS) {
            // Read the photodiode value
            int value = analogRead(i);

            // Add the value to the state
            state = (state << 1);
            if (value > PHOTODIODE_TRESHOLD) {
                state |= 0x1;
            }
        }
    }
    Wire.write(state);
}

void loop() {
#ifdef DEBUG
    printDebugInfo();
#endif

    // Check if motor1 has hit a limit
    if (motor1.isMoving() && motor1.getDirection() == MotorDirection::UP && digitalRead(MOTOR1_TOP_LIMIT) == LOW) {
        motor1.stopMotor();
        motor1.clearErrorState();
    } else if (motor1.isMoving() && motor1.getDirection() == MotorDirection::DOWN &&
               (digitalRead(MOTOR1_LOWER_LIMIT) == LOW)) {
        motor1.stopMotor();
        motor1.clearErrorState();
    }

    // Check if motor2 has hit a limit
    if (motor2.isMoving() && motor2.getDirection() == MotorDirection::UP && digitalRead(MOTOR2_TOP_LIMIT) == LOW) {
        motor2.stopMotor();
        motor2.clearErrorState();
    } else if (motor2.isMoving() && motor2.getDirection() == MotorDirection::DOWN &&
               digitalRead(MOTOR2_LOWER_LIMIT) == LOW) {
        motor2.stopMotor();
        motor2.clearErrorState();
    }

    // Check if the motor1 has been running for longer than MOTOR_TIMEOUT_MILLI
    if (motor1.isMoving() && motor1.getRunningTime() > MOTOR_TIMEOUT_MILLI) {
        motor1.stopMotor();
        motor1.setErrorState();
    }

    // Check if the motor2 has been running for longer than MOTOR_TIMEOUT_MILLI
    if (motor2.isMoving() && motor2.getRunningTime() > MOTOR_TIMEOUT_MILLI) {
        motor2.stopMotor();
        motor2.setErrorState();
    }
}

void printDebugInfo() {
    static uint32_t lastPrintout;
    if (millis() - lastPrintout <
        5000) { // Do not print if it has not been more than 5 seconds since the last time we did it
        return;
    }
    PRINTLN("Motor 1 status");
    PRINT("Moving: ");
    PRINTLN(motor1.isMoving());
    PRINT("Direction: ");
    PRINTLN(motor1.getDirection());


    PRINTLN("Motor 2 status");
    PRINT("Moving: ");
    PRINTLN(motor2.isMoving());
    PRINT("Direction: ");
    PRINTLN(motor2.getDirection());

    PRINT("State that would be sent to RPi: ");
    PRINTLN((motor1.isMoving() << 3) | (motor1.isInErrorState() << 2) | (motor2.isMoving() << 1) |
            motor2.isInErrorState(), BIN);
    PRINTLN("\n");
    lastPrintout = millis(); // Update the last time we printed the debug info

	uint8_t state = 0;
	for (auto i : PHOTODIODE_PORTS) {
		// Read the photodiode value
		auto value = analogRead(i);

        // Add the value to the state
        state = (state << 1);
        if (value > PHOTODIODE_TRESHOLD) {
            state |= 0x1;
        }
	}

	PRINT("LED State: ");
	PRINT(state);
	PRINTLN("\n");
}