#include "motor.h"

// The duty cycle when the motor is moving. When stopped, it will always be at the maximum (255)
const uint8_t PWM_DUTY_CYCLE = 255;

boolean inline isLimitPressed(uint8_t limitPin) {
    return digitalRead(limitPin) == LOW;
}

Motor::Motor(uint8_t enPin, uint8_t int1Pin, uint8_t int2Pin, uint8_t topLimit, uint8_t lowerLimit, u_int16_t timeout) 
    : enPin(enPin), int1Pin(int1Pin), int2Pin(int2Pin), topLimit(topLimit), lowerLimit(lowerLimit), timeout(timeout) {
    pinMode(enPin, OUTPUT);
    pinMode(int1Pin, OUTPUT);
    pinMode(int2Pin, OUTPUT);
}

void Motor::startMotor(MotorDirection startDirection) volatile {
    // Don't continue if the limit is pressed in the startDirection we want to go
    if ((startDirection == MotorDirection::UP && isLimitPressed(topLimit)) ||
        (startDirection == MotorDirection::DOWN && isLimitPressed(lowerLimit))) {
        return;
    }

    analogWrite(enPin, PWM_DUTY_CYCLE);
    if (startDirection == MotorDirection::UP) {
        digitalWrite(int1Pin, HIGH);
        digitalWrite(int2Pin, LOW);
    } else {
        digitalWrite(int1Pin, LOW);
        digitalWrite(int2Pin, HIGH);
    }

    this->moving = true;
    this->direction = startDirection;
    this->startTime = millis();
}

void Motor::stopMotor() volatile {
    digitalWrite(int1Pin, LOW);
    digitalWrite(int2Pin, LOW);
    analogWrite(enPin, 255);

    this->moving = false;
}

void Motor::checkState() {
    if (isMoving()) {
        // Check if motor has hit a limit
        if ((getDirection() == MotorDirection::UP && isLimitPressed(topLimit)) ||
            (getDirection() == MotorDirection::DOWN && isLimitPressed(lowerLimit))) {
            stopMotor();
            clearErrorState();
        }

        // Check if we ran longer than allowed
        if (getRunningTime() > timeout) {
            stopMotor();
            setErrorState();
        }
    }
}

boolean Motor::isMoving() const volatile {
    return moving;
}

MotorDirection Motor::getDirection() const volatile {
    return direction;
}

unsigned long Motor::getRunningTime() const volatile {
    return millis() - startTime;
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
