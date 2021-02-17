#ifndef ARDUINO_MAIN_H
#define ARDUINO_MAIN_H

void setup();

void loop();

void receiveI2CEvent(int numBytes);

void sendI2CState();

void printDebugInfo();

enum I2CSendingValue {
    MOTOR = 0x0,
    LED = 0x1,
};

#endif //ARDUINO_MAIN_H
