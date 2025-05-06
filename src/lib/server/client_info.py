from lib.utils.constants import OPERATION
from io import BufferedRandom
from lib.utils.types import ADDR
from dataclasses import dataclass
from lib.utils.enums import PackageType


@dataclass
class ClientInfo:
    addr: ADDR
    operation: OPERATION
    file_descriptor: int
    last_package_type: PackageType
    filename: str
    file: BufferedRandom | None = None
    protocol_handler: object | None = None
