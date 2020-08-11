#include <Arduino.h>
#include <Wire.h>
#include "main.h"
#include "debug.h"
#include "motor.h"

// Ports for the limit switches. These uses the internal port of the ATMega microcontroller
// The motor 1 pins will reside on one of the PORT B, and motor 2 pins reside on PORT D. This allows to have two
// separate pin change interrupts, because pin change interrupts can only be configured on a whole port.
// See https://www.arduino.cc/en/Hacking/PinMapping168 for the pin mapping

// PORT B (digital pins 8 to 13)
const uint8_t MOTOR1_TOP_LIMIT = 0;
const uint8_t MOTOR1_LOWER_LIMIT = 1;

// PORT D (digital pins 0 to 7)
const uint8_t MOTOR2_TOP_LIMIT = 0;
const uint8_t MOTOR2_LOWER_LIMIT = 1;

// If we should enable the internal pullup resistors. For testing, this may be needed, but the final board will have
// its own pullup resistors, so this should be false.
const bool ENABLE_PULLUP_RESISTORS = false;

// Ports for the motors. These uses the standard Arduino pin numbers
const uint8_t MOTOR1_EN = 3;
const uint8_t MOTOR1_IN1 = 2;
const uint8_t MOTOR1_IN2 = 4;
const uint8_t MOTOR2_EN = 5;
const uint8_t MOTOR2_IN1 = 6;
const uint8_t MOTOR2_IN2 = 7;

// Communication settings
const uint8_t I2C_ADDRESS = 0x2;
const uint64_t SERIAL_RATE = 9600;

volatile Motor motor1(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2);
volatile Motor motor2(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2);

// Pin Change Interrupt for Port B (motor 1). PCINT0..7
ISR(PCINT0_vect) {
    if (motor1.isMoving() && motor1.getDirection() == MotorDirection::UP && ((PINB >> MOTOR1_TOP_LIMIT) & 1) == 0) {
        motor1.stopMotor();
    } else if (motor1.isMoving() && motor1.getDirection() == MotorDirection::DOWN &&
               ((PINB >> MOTOR1_LOWER_LIMIT) & 1) == 0) {
        motor1.stopMotor();
    }
}

// Pin Change Interrupt for Port D (motor 2). PCINT16..23
ISR(PCINT2_vect) {
    if (motor2.isMoving() && motor2.getDirection() == MotorDirection::UP && ((PIND >> MOTOR2_TOP_LIMIT) & 1) == 0) {
        motor2.stopMotor();
    } else if (motor2.isMoving() && motor2.getDirection() == MotorDirection::DOWN &&
               ((PIND >> MOTOR2_LOWER_LIMIT) & 1) == 0) {
        motor2.stopMotor();
    }
}

void setup() {
    // Set the limit switch pins as an input by setting the appropriate bit at 0
    DDRB &= ~((1 << MOTOR1_TOP_LIMIT) | (1 << MOTOR1_LOWER_LIMIT));
    DDRD &= ~((1 << MOTOR2_TOP_LIMIT) | (1 << MOTOR2_LOWER_LIMIT));

    if (ENABLE_PULLUP_RESISTORS) {
        PORTB |= (1 << MOTOR1_TOP_LIMIT) | (1 << MOTOR1_LOWER_LIMIT);
        PORTD |= (1 << MOTOR2_TOP_LIMIT) | (1 << MOTOR2_LOWER_LIMIT);
    }

    // Enable the Pin Change interrupts
    PCICR |= (1 << PCIE0) | (1 << PCIE2);
    PCMSK0 |= (1 << MOTOR1_TOP_LIMIT) | (1 << MOTOR1_LOWER_LIMIT);
    PCMSK2 |= (1 << MOTOR2_TOP_LIMIT) | (1 << MOTOR2_LOWER_LIMIT);

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
#ifdef DEBUG
    delay(5000);
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
    PRINTLN("\n");
#endif
}