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
        return f"{self.type.value}{SEPARATOR}{self.data}".encode("utf-8")
