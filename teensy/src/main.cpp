#include <Arduino.h>
#include <i2c_driver_wire.h>
#include "main.h"
#include "debug.h"
#include "motor.h"

// Ports for the motors.
const uint8_t MOTOR1_EN = 4;
const uint8_t MOTOR1_IN1 = 5;
const uint8_t MOTOR1_IN2 = 6;
const uint8_t MOTOR2_EN = 7;
const uint8_t MOTOR2_IN1 = 8;
const uint8_t MOTOR2_IN2 = 9;

// Limit switches for the motors
const uint8_t MOTOR1_TOP_LIMIT = 3;
const uint8_t MOTOR1_LOWER_LIMIT = 2;
const uint8_t MOTOR2_TOP_LIMIT = 1;
const uint8_t MOTOR2_LOWER_LIMIT = 0;

// Ports for the photodiodes. On a I2C read, the data will be sent in the listed order.
const uint8_t PHOTODIODE_PORTS[] = {
       22, //MSB
       21,
       20,
       17,
       16,
       15,
       14  //LSB
};

// Threshold at which the photodiodes should be recognized as HIGH.
const int PHOTODIODE_TRESHOLD = 900;

// Communication settings
const uint8_t I2C_ADDRESS = 0x8;
const uint64_t SERIAL_RATE = 9600;

// How long to wait in milliseconds before stopping a motor automatically
const uint16_t MOTOR_TIMEOUT_MILLI = 45 * 1000;

// Store what we should send to the Pi for the i2C value
I2CSendingValue i2cSendingValue = I2CSendingValue::MOTOR;

Motor motor1(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2, MOTOR1_TOP_LIMIT, MOTOR1_LOWER_LIMIT, MOTOR_TIMEOUT_MILLI);
Motor motor2(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2, MOTOR2_TOP_LIMIT, MOTOR2_LOWER_LIMIT, MOTOR_TIMEOUT_MILLI);

void setup() {
    // Setup the Teensy as an i2c slave
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveI2CEvent);
    Wire.onRequest(sendI2CState);

    // Enable the internal pulldown resistors for the photodiodes
    for (auto i : PHOTODIODE_PORTS) {
        pinMode(i, INPUT_PULLUP);
    }

    pinMode(MOTOR1_TOP_LIMIT, INPUT_PULLUP);
    pinMode(MOTOR1_LOWER_LIMIT, INPUT_PULLUP);
    pinMode(MOTOR2_TOP_LIMIT, INPUT_PULLUP);
    pinMode(MOTOR2_LOWER_LIMIT, INPUT_PULLUP);

    pinMode(13, OUTPUT);
    digitalWrite(13, HIGH);

#ifdef DEBUG
    Serial.begin(SERIAL_RATE);
#endif
}

uint8_t lastRead = 0;

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

        lastRead = data;

        if ((data >> 2) & 1) { // This is a motor control event
            uint8_t motorNumber = (data >> 1) & 1;
            auto motorDirection = static_cast<MotorDirection>(data & 1);

            if (motorNumber == 0) {
                motor1.startMotor(motorDirection);
            } else {
                motor2.startMotor(motorDirection);
            }
        } else { // Change what a i2c read will send
            i2cSendingValue = static_cast<I2CSendingValue>(data & 1);
        }
    }
}

// The sent state depends on the content of the i2cSendingValue variable.
// If sending the motor state:
//      Sends the motors state to the RPi in a 4 bit number, 2 bit for each motor.
//      The MSB of a motor is set to 1 if that motor is moving. The LSB is set to 1 if that motor is in an error state.
//      The two most significant bits are for motor 1, the other two LSB are for motor 2.
//      For example, if motor 1 is not moving and in an error state, and motor 2 is moving and not in error state, 0110 will be sent
// If sending the LED state:
//      The state of each LED is represented by a 0 (OFF) or 1 (ON).
//      See the PHOTODIODE_PORTS variable for the order of the LEDs.
void sendI2CState() {
    uint8_t state = 0;
    if (i2cSendingValue == I2CSendingValue::MOTOR) {
        state = (motor1.isMoving() << 3) | (motor1.isInErrorState() << 2) | (motor2.isMoving() << 1) |
                motor2.isInErrorState();
    } else if (i2cSendingValue == I2CSendingValue::LED) {
        for (auto i : PHOTODIODE_PORTS) {
            // Read the photodiode value
            int value = analogRead(i);

            // Add the value to the state
            state = (state << 1);
            if (value < PHOTODIODE_TRESHOLD) {
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
	motor1.checkState();
	motor2.checkState();
}

void printDebugInfo() {
    static uint32_t lastPrintout;
    if (millis() - lastPrintout <
        500) { // Do not print if it has not been more than 0.5 seconds since the last time we did it
        return;
    }

    PRINT("Last Read: ");
    PRINT(lastRead);
    PRINTLN("");

    PRINTLN("Limit status:");
    PRINT(isLimitPressed(MOTOR1_TOP_LIMIT));
    PRINT(isLimitPressed(MOTOR1_LOWER_LIMIT));
    PRINT(isLimitPressed(MOTOR2_TOP_LIMIT));
    PRINT(isLimitPressed(MOTOR2_LOWER_LIMIT));
    PRINTLN("");

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
        if (value < PHOTODIODE_TRESHOLD) {
            state |= 0x1;
        }
        PRINTLN(value);
	}

	PRINT("LED State: ");
	PRINT(state);
	PRINTLN("\n");
}