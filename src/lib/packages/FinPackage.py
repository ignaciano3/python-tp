from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR
from lib.packages.Package import Package


class FinPackage(Package):
    def __init__(
        self,
    ) -> None:
        super().__init__(PackageType.FIN)

    def to_bytes(self) -> bytes:
        return f"{self.type.value}{SEPARATOR}".encode("utf-8")