from lib.packages.Package import Package
from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR
from lib.utils.package_error import PackageErr, ChecksumErr


class DataPackage(Package):
    def __init__(self, data: bytes, sequence_number: int):
        super().__init__(PackageType.DATA, data)
        self.data = data
        self.sequence_number = sequence_number

    def to_bytes(self) -> bytes:
        if self.data is None:
            raise ValueError("Data is not set")
        # Codifica como: DATA|<sequence_number>|<payload>
        checksum = self.get_checksum()
        return (
            f"{self.type.value}{SEPARATOR}{self.sequence_number}{SEPARATOR}{checksum}{SEPARATOR}".encode(
                "utf-8"
            )
            + self.data
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> "DataPackage":
        try:
            parts = raw.split(SEPARATOR.encode(), 3)
            if len(parts) < 4:
                raise PackageErr("Incomplete package")

            _, seq_num_bytes, checksum_bytes, payload = parts
            sequence_number = int(seq_num_bytes.decode("utf-8"))
            checksum = int(checksum_bytes.decode("utf-8"))

            instance = cls(payload, sequence_number)
            if instance.get_checksum() != checksum:
                raise ChecksumErr("Checksum does not match")

            return instance

        except (ValueError, IndexError) as e:
            raise PackageErr(f"Failed to parse DataPackage: {e}") from e
