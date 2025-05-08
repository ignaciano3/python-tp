from lib.utils.constants import OPERATION, SEPARATOR
from lib.packages.Package import Package
from lib.utils.enums import PackageType


class InitPackage(Package):
    def __init__(
        self,
        operation: OPERATION,
        file_name: str,
    ) -> None:
        self.operation: OPERATION = operation
        self.file_name = file_name
        super().__init__(PackageType.INIT)

    def get_file_name_without_extension(self) -> str:
        return self.file_name.split(".")[0]

    def get_file_extension(self) -> str:
        return self.file_name.split(".")[-1]

    def to_bytes(self) -> bytes:
        filename_without_extension = self.get_file_name_without_extension()
        file_extension = self.get_file_extension()
        header = f"{self.type.value}{SEPARATOR}{self.operation}{SEPARATOR}{filename_without_extension}{SEPARATOR}{file_extension}"
        return header.encode("utf-8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> "InitPackage":
        received = raw.decode("utf-8")
        parts = received.split(SEPARATOR)

        if len(parts) != 4:
            raise ValueError("Invalid header format")

        if parts[1] != "upload" and parts[1] != "download":
            raise ValueError("Invalid operation. Use 'upload' or 'download'.")

        operation: OPERATION = parts[1]
        file_name = f"{parts[2]}.{parts[3]}"

        return cls(operation, file_name)


class UploadHeader(InitPackage):
    def __init__(self, file_name: str) -> None:
        super().__init__("upload", file_name)


class DownloadHeader(InitPackage):
    def __init__(self, file_name: str) -> None:
        super().__init__("download", file_name)
