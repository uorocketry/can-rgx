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
const uint8_t MOTOR2_TOP_LIMIT = 2;
const uint8_t MOTOR2_LOWER_LIMIT = 3;

// If we should enable the internal pullup resistors. For testing, this may be needed, but the final board will have
// its own pullup resistors, so this should be false.
const bool ENABLE_PULLUP_RESISTORS = false;

// Ports for the motors. These uses the standard Arduino pin numbers. Please do not use pin 9 or 10 for the EN pins,
// because this could possibly cause conflicts with the timer.
const uint8_t MOTOR1_EN = 5;
const uint8_t MOTOR1_IN1 = 4;
const uint8_t MOTOR1_IN2 = 6;
const uint8_t MOTOR2_EN = 10;
const uint8_t MOTOR2_IN1 = 11;
const uint8_t MOTOR2_IN2 = 12;

// Communication settings
const uint8_t I2C_ADDRESS = 0x2;
const uint64_t SERIAL_RATE = 9600;

// How long to wait in milliseconds before stopping a motor automatically
const volatile uint16_t MOTOR_TIMEOUT_MILLI = 10 * 1000;

volatile Motor motor1(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2);
volatile Motor motor2(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2);

// Pin Change Interrupt for Port B (motor 1). PCINT0..7
ISR(PCINT0_vect) {
    if (motor1.isMoving() && motor1.getDirection() == MotorDirection::UP && ((PINB >> MOTOR1_TOP_LIMIT) & 1) == 0) {
        motor1.stopMotor();
        motor1.clearErrorState();
    } else if (motor1.isMoving() && motor1.getDirection() == MotorDirection::DOWN &&
               ((PINB >> MOTOR1_LOWER_LIMIT) & 1) == 0) {
        motor1.stopMotor();
        motor1.clearErrorState();
    }
}

// Pin Change Interrupt for Port D (motor 2). PCINT16..23
ISR(PCINT2_vect) {
    if (motor2.isMoving() && motor2.getDirection() == MotorDirection::UP && ((PIND >> MOTOR2_TOP_LIMIT) & 1) == 0) {
        motor2.stopMotor();
        motor2.clearErrorState();
    } else if (motor2.isMoving() && motor2.getDirection() == MotorDirection::DOWN &&
               ((PIND >> MOTOR2_LOWER_LIMIT) & 1) == 0) {
        motor2.stopMotor();
        motor2.clearErrorState();
    }
}

// Checks every 0.2 s (5Hz) if the motor ran for too long
ISR(TIMER1_COMPA_vect) {
    if (motor1.isMoving() && motor1.getRunningTime() > MOTOR_TIMEOUT_MILLI) {
        motor1.stopMotor();
        motor1.setErrorState();
    }

    if (motor2.isMoving() && motor2.getRunningTime() > MOTOR_TIMEOUT_MILLI) {
        motor2.stopMotor();
        motor2.setErrorState();
    }
}

void setup() {
    noInterrupts();
    // Set the limit switch pins as an input by setting the appropriate bit at 0
    DDRB &= ~((1 << MOTOR1_TOP_LIMIT) | (1 << MOTOR1_LOWER_LIMIT));
    DDRD &= ~((1 << MOTOR2_TOP_LIMIT) | (1 << MOTOR2_LOWER_LIMIT));

    if (ENABLE_PULLUP_RESISTORS) {
        PORTB |= (1 << MOTOR1_TOP_LIMIT) | (1 << MOTOR1_LOWER_LIMIT);
        PORTD |= (1 << MOTOR2_TOP_LIMIT) | (1 << MOTOR2_LOWER_LIMIT);
    }

    // Enable the Pin Change interrupts
    PCICR |= (1 << PCIE0) | (1 << PCIE2); //Enable the actual interrupt on Port B and D
    PCMSK0 |= (1 << MOTOR1_TOP_LIMIT) | (1 << MOTOR1_LOWER_LIMIT); // Allow the appropriate pins to trigger the interrupt
    PCMSK2 |= (1 << MOTOR2_TOP_LIMIT) | (1 << MOTOR2_LOWER_LIMIT);


    // Setup Timer 1 to run the interrupt at 2Hz. See this site for more info: https://oscarliang.com/arduino-timer-and-interrupt-tutorial/
    TCCR1A = 0;
    TCCR1B = 0;
    OCR1A = 12500; // Set the timer to reset when it hits this value. This should make it reset at 5Hz
    TCCR1B |= (1 << WGM12) | (1 << CS12); // Configure the CTC (clear timer on compare match) mode and a prescaler of 256
    TIMSK1 |= (1 << OCIE1A); // Enable the output compare A match interrupt

    // Setup the Arduino as an i2c slave
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveI2CEvent);
    Wire.onRequest(sendI2CState);

#ifdef DEBUG
    Serial.begin(SERIAL_RATE);
#endif
    interrupts();
}

// This function expects to receive two bits from I2C. The MSB represents the motorNumber (0 for motor 1 and 1 for motor 2)
// THE LSB represents the motor direction. 0 is UP, 1 is DOWN
void receiveI2CEvent(int) {
    while (Wire.available()) {
        uint8_t data = Wire.read();

        uint8_t motorNumber = (data >> 1) & 1;
        auto motorDirection = static_cast<MotorDirection>(data & 1);

        if (motorNumber == 0) {
            // Only start the motor if the limit is not pressed
            if (!(motorDirection == MotorDirection::UP && ((PINB >> MOTOR1_TOP_LIMIT) & 1) == 0) &&
                !(motorDirection == MotorDirection::DOWN && ((PINB >> MOTOR1_LOWER_LIMIT) & 1) == 0)) {
                motor1.startMotor(motorDirection);
            }
        } else {
            // Only start the motor if the limit is not pressed
            if (!(motorDirection == MotorDirection::UP && ((PIND >> MOTOR2_TOP_LIMIT) & 1) == 0) &&
                !(motorDirection == MotorDirection::DOWN && ((PIND >> MOTOR2_LOWER_LIMIT) & 1) == 0)) {
                motor2.startMotor(motorDirection);
            }
        }
    }
}

// Sends the motors state to the RPi in a 4 bit number, 2 bit for each motor.
// The MSB of a motor is set to 1 if that motor is moving. The LSB is set to 1 if that motor is in an error state.
// The two most significant bits are for motor 1, the other two LSB are for motor 2.
// For example, if motor 1 is not moving and in an error state, and motor 2 is moving and not in error state, 0110 will be sent
void sendI2CState() {
    uint8_t state = (motor1.isMoving() << 3) | (motor1.isInErrorState() << 2) | (motor2.isMoving() << 1) | motor2.isInErrorState();

    Wire.write(state);
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

    PRINT("State that would be sent to RPi: ");
    PRINTLN((motor1.isMoving() << 3) | (motor1.isInErrorState() << 2) | (motor2.isMoving() << 1) | motor2.isInErrorState(), BIN);
    PRINTLN("\n");
#endif
}