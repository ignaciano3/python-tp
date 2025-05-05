from lib.packages.Package import Package
from lib.utils.enums import PackageType
from lib.utils.constants import SEPARATOR


class DataPackage(Package):
    def __init__(self, data: bytes, sequence_number: int):
        super().__init__(PackageType.DATA, data)
        self.data = data
        self.sequence_number = sequence_number

    def to_bytes(self) -> bytes:
        if self.data is None:
            raise ValueError("Data is not set")
        # Codifica como: DATA|<sequence_number>|<payload>
        return (
            f"{self.type.value}{SEPARATOR}{self.sequence_number}{SEPARATOR}".encode(
                "utf-8"
            )
            + self.data
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> "DataPackage":
        try:
            header, payload = (
                raw.split(SEPARATOR.encode(), 2)[0:2],
                raw.split(SEPARATOR.encode(), 2)[2],
            )
            _, seq_num_str = header
            return cls(payload, int(seq_num_str.decode("utf-8")))
        except Exception as e:
            raise ValueError(f"Failed to parse DataPackage: {e}")
