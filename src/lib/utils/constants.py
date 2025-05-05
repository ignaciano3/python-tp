from typing import Literal


BUFSIZE = 1500
OPERATION = Literal[
    "upload",
    "download",
]
DEFAULT_HOST = "localhost"
CLIENT_STORAGE = "src/lib/client_storage"
SERVER_STORAGE = "src/lib/server_storage"
DEFAULT_PORT = 8080
SEPARATOR = "|"