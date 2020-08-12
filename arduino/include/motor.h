#ifndef ARDUINO_MOTOR_H
#define ARDUINO_MOTOR_H

#include <Arduino.h>

enum MotorDirection {
    UP = 0x0,
    DOWN = 0x1
};

class Motor {
public:
    Motor(uint8_t enPin, uint8_t int1Pin, uint8_t int2Pin);

    void startMotor(MotorDirection direction) volatile;

    void stopMotor() volatile;

    boolean isMoving() const volatile;

    MotorDirection getDirection() const volatile;

    unsigned long getRunningTime() const volatile;

    bool isInErrorState() const volatile;

    void setErrorState() volatile;

    void clearErrorState() volatile;

private:
    const uint8_t enPin;
    const uint8_t int1Pin;
    const uint8_t int2Pin;

    bool moving = false;
    MotorDirection direction = MotorDirection::UP;

    unsigned long startTime = 0;

    // Represent if a motor is in some kind of general error state, for example it got stopped because of the timer
    // instead of the limit switch, possibly indicating a failure of the limit switch
    bool inErrorState = false;
};


#endif //ARDUINO_MOTOR_H
