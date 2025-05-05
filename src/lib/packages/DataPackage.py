from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR
from lib.packages.Package import Package


class DataPackage(Package):
    def __init__(
        self,
        data: bytes,
    ) -> None:
        super().__init__(PackageType.DATA, data)

    def to_bytes(self) -> bytes:
        if self.data is None:
            raise ValueError("Data is not set")
        return f"{self.type.value}{SEPARATOR}{self.data.decode("utf-8")}".encode("utf-8")
