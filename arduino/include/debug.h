#ifndef ARDUINO_DEBUG_H
#define ARDUINO_DEBUG_H

// Uncomment the following line to enable debug messages
//#define DEBUG

#ifdef DEBUG
#define PRINTLN(args...) Serial.println(args)
#define PRINT(args...) Serial.print(args)
#else
#define PRINTLN(x)
#define PRINT(x)
#endif

#endif //ARDUINO_DEBUG_H
