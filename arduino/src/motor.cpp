#include "motor.h"

// The duty cycle when the motor is moving. When stopped, it will always be at the maximum (255)
const uint8_t PWM_DUTY_CYCLE = 255;

Motor::Motor(uint8_t enPin, uint8_t int1Pin, uint8_t int2Pin) : enPin(enPin), int1Pin(int1Pin), int2Pin(int2Pin) {
    pinMode(enPin, OUTPUT);
    pinMode(int1Pin, OUTPUT);
    pinMode(int2Pin, OUTPUT);
}

void Motor::startMotor(MotorDirection direction) volatile {
    analogWrite(enPin, PWM_DUTY_CYCLE);
    if (direction == MotorDirection::UP) {
        digitalWrite(int1Pin, HIGH);
        digitalWrite(int2Pin, LOW);
    } else {
        digitalWrite(int1Pin, LOW);
        digitalWrite(int2Pin, HIGH);
    }

    this->moving = true;
    this->direction = direction;
    this->startTime = millis();
}

void Motor::stopMotor() volatile {
    digitalWrite(int1Pin, LOW);
    digitalWrite(int2Pin, LOW);
    analogWrite(enPin, 255);

    this->moving = false;
}

boolean Motor::isMoving() const volatile {
    return moving;
}

MotorDirection Motor::getDirection() const volatile {
    return direction;
}

unsigned long Motor::getRunningTime() const volatile {
    return millis()-startTime;
}

bool Motor::isInErrorState() const volatile {
    return inErrorState;
}

void Motor::setErrorState() volatile {
    inErrorState = true;
}

void Motor::clearErrorState() volatile {
    inErrorState = false;
}
