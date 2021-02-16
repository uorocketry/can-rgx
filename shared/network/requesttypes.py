from enum import IntEnum


class RequestTypes(IntEnum):
    PING = 0
    CONTROLMOTOR = 1
    CONTROLLED = 2
