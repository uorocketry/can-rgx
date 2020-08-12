#ifndef ARDUINO_MAIN_H
#define ARDUINO_MAIN_H
void setup();

void loop();

void receiveI2CEvent(int numBytes);

void sendI2CState();

#endif //ARDUINO_MAIN_H
