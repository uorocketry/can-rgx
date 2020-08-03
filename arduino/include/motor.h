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

    void startMotor(MotorDirection direction);

    void stopMotor();

private:
    const uint8_t enPin;
    const uint8_t int1Pin;
    const uint8_t int2Pin;
};

#endif //ARDUINO_MOTOR_H
