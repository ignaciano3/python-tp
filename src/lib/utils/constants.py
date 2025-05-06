from typing import Literal
from enum import Enum


BUFSIZE = 1500
OPERATION = Literal[
    "upload",
    "download",
]
DEFAULT_HOST = LOCALHOST = "localhost"
CLIENT_STORAGE = "src/lib/client_storage"
SERVER_STORAGE = "src/lib/server_storage"
DEFAULT_PORT = 8080
SEPARATOR = "|"
TIMEOUT = 10000


class Protocol(Enum):
    STOP_WAIT = 0
    SELECTIVE_REPEAT = 1
