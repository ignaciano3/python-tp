from enum import Enum


class Protocol(Enum):
    STOP_WAIT = 0
    SELECTIVE_REPEAT = 1


class PackageType(Enum):
    INIT = "INIT"
    DATA = "DATA"
    ACK = "ACK"
    NACK = "NACK"
    FIN = "FIN"

    @staticmethod
    def from_bytes(data: bytes) -> "PackageType":
        return PackageType(int.from_bytes(data, byteorder="big"))
