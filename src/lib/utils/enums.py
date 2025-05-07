from enum import Enum


class Protocol(Enum):
    STOP_WAIT = 0
    SELECTIVE_REPEAT = 1




class PackageType(Enum):
    INIT = 0
    DATA = 1
    ACK = 2
    NACK = 3
    FIN = 4

    @staticmethod
    def from_bytes(data: bytes) -> "PackageType":
        return PackageType(int.from_bytes(data, byteorder="big"))
