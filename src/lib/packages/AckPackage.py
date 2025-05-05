from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR
from lib.packages.Package import Package


class AckPackage(Package):
    def __init__(
        self,
        sequence_number: int = 0,
    ) -> None:
        super().__init__(PackageType.ACK)
        self.sequence_number = sequence_number

    def to_bytes(self) -> bytes:
        return f"{self.type.value}{SEPARATOR}{self.sequence_number}".encode("utf-8")

    @staticmethod
    def from_bytes(data: bytes) -> "AckPackage":
        # Separamos la información del tipo de paquete y el número de secuencia
        parts = data.decode("utf-8").split(SEPARATOR)
        sequence_number = int(parts[1])
        return AckPackage(sequence_number)
