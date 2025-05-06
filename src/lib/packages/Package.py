from lib.utils.enums import PackageType
from lib.utils.constants import BUFSIZE


class Package:
    data = None

    def __init__(self, type: PackageType, data: bytes | None = None) -> None:
        self.type = type
        if data is not None and len(data) > BUFSIZE:
            raise ValueError("Data size exceeds buffer size")

        self.data = data

    def set_data(self, data: bytes) -> None:
        self.data = data

    def to_bytes(self) -> bytes:
        raise NotImplementedError("Subclasses should implement this method")

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Package":
        raise NotImplementedError("Subclasses should implement this method")
