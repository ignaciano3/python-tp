from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR
from lib.packages.Package import Package


class AckPackage(Package):
    def __init__(
        self,
    ) -> None:
        super().__init__(PackageType.ACK)

    def to_bytes(self) -> bytes:
        return f"{self.type.value}{SEPARATOR}".encode("utf-8")