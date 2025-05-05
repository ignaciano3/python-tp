from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR
from lib.packages.Package import Package


class DataPackage(Package):
    def __init__(
        self,
        data: bytes,
    ) -> None:
        super().__init__(PackageType.DATA, data)
        self.data = data

    def to_bytes(self) -> bytes:
        if self.data is None:
            raise ValueError("Data is not set")
        return f"{self.type.value}{SEPARATOR}{self.data.decode('utf-8')}".encode(
            "utf-8"
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> "DataPackage":
        try:
            parts = raw.decode("utf-8").split(SEPARATOR, 1)
            if len(parts) != 2:
                raise ValueError("Invalid DataPackage format")
            _, payload_str = parts
            return cls(payload_str.encode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse DataPackage: {e}")
