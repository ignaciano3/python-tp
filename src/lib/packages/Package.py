from lib.utils.enums import PackageType
from lib.utils.constants import BUFSIZE, SEPARATOR


class Package:
    data = None

    def __init__(
        self,
        type: PackageType,
        data: bytes | None = None,
        valid: bool = True,
        sequence_number: int = 0,
    ) -> None:
        self.sequence_number = sequence_number
        self.type = type
        self.valid = valid
        if data is not None and len(data) > BUFSIZE:
            raise ValueError("Data size exceeds buffer size")
        self.data = data

    def set_data(self, data: bytes) -> None:
        self.data = data

    def get_checksum(self) -> int:
        if self.data is None:
            return 0

        return sum(self.data) % 256

    def to_bytes(self) -> bytes:
        raise NotImplementedError("Subclasses should implement this method")

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Package":
        raise NotImplementedError("Subclasses should implement this method")

    @classmethod
    def get_type(cls, package_raw: bytes) -> PackageType:
        package_type_raw = package_raw.decode("utf-8").split(SEPARATOR)[0]
        return PackageType(int(package_type_raw))

    def __repr__(self) -> str:
        return f"Package(type={self.type}, sequence_number={self.sequence_number}, valid={self.valid})"
