from enum import IntEnum

class RequestTypes(IntEnum):
    PING = 0
    CONNECTLOGGING = 1
    CONTROLMOTOR = 2
    CONTROLLED = 3
