#include <Arduino.h>
#include <i2c_driver_wire.h>
#include "main.h"
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
const int PHOTODIODE_TRESHOLD = 990;

// Communication settings
const uint8_t I2C_ADDRESS = 0x8;
const uint64_t SERIAL_RATE = 9600;

// How long to wait in milliseconds before stopping a motor automatically
const uint32_t MOTOR_TIMEOUT_MILLI = 60 * 1000;

// Store what we should send to the Pi for the i2C value
I2CSendingValue i2cSendingValue = I2CSendingValue::MOTOR;

Motor motor1(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2, MOTOR1_TOP_LIMIT, MOTOR1_LOWER_LIMIT, MOTOR_TIMEOUT_MILLI);
Motor motor2(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2, MOTOR2_TOP_LIMIT, MOTOR2_LOWER_LIMIT, MOTOR_TIMEOUT_MILLI);

void setup() {
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

    Serial.begin(115200);
}

uint8_t lastRead = 0;

void checkForMessage() {
    if (Serial.available() > 0) {
        String data_str = Serial.readStringUntil('\n');
        int data = data_str.toInt();

        int check = (data >> 2) & 0b1111;
        if (check != 0b1001) {
            // Ignore if we don't start with this sequence of bits
            // This is to prevent occasional times where the Teensy reads a command
            // when there is none
            return;
        }

        uint8_t motorNumber = (data >> 1) & 1;
        auto motorDirection = static_cast<MotorDirection>(data & 1);

        if (motorNumber == 0) {
            motor1.startMotor(motorDirection);
        } else {
            motor2.startMotor(motorDirection);
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
void sendState() {
    uint16_t state = (isLimitPressed(MOTOR1_TOP_LIMIT) << 3) | (isLimitPressed(MOTOR1_LOWER_LIMIT) << 2) |
            (isLimitPressed(MOTOR2_TOP_LIMIT) << 1) | (isLimitPressed(MOTOR2_LOWER_LIMIT));

    state = state << 4;

    state |= (motor1.isMoving() << 3) | (motor1.isInErrorState() << 2) | (motor2.isMoving() << 1) |
            motor2.isInErrorState();

    for (auto i : PHOTODIODE_PORTS) {
        // Read the photodiode value
        int value = analogRead(i);

        // Add the value to the state
        state = (state << 1);
        if (value < PHOTODIODE_TRESHOLD) {
            state |= 0x1;
        }
    }

    Serial.println(state);
}

void loop() {
    sendState();
    checkForMessage();
	motor1.checkState();
	motor2.checkState();
	delay(50);
}