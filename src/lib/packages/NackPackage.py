from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR
from lib.packages.Package import Package


class NackPackage(Package):
    def __init__(self, sequence_number: int = 0) -> None:
        super().__init__(PackageType.NACK, valid=False, sequence_number=sequence_number)

    def to_bytes(self) -> bytes:
        return f"{self.type.value}{SEPARATOR}{self.sequence_number}{SEPARATOR}{self.valid}".encode(
            "utf-8"
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> "NackPackage":
        parts = raw.decode("utf-8").split(SEPARATOR)
        sequence_number = int(parts[1])
        return cls(sequence_number)
