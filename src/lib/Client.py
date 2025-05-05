import logging
from typing import Literal

from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.common.Upload import Upload
from lib.utils.constants import DEFAULT_PORT, DEFAULT_HOST, CLIENT_STORAGE
from lib.common.Download import Download
from lib.utils.enums import Protocol


class Client:
    def __init__(
        self,
        operation: Literal["upload", "download"],
        file_path: str = "",
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        protocol: Protocol = Protocol.STOP_WAIT,
        client_storage: str = CLIENT_STORAGE,
        logging_level=logging.DEBUG,
    ) -> None:
        self.host = host
        self.port = port
        self.operation = operation
        self.logging_level = logging_level
        self.logger = create_logger("client", "[CLIENT]", logging_level)
        self.socket = Socket(logging_level)
        self.file_path = file_path
        self.client_storage = client_storage
        self.protocol = protocol

        if self.operation == 'upload':
            self.operator = Upload(self.file_path, self.socket, (self.host, self.port), self.logging_level)
        elif self.operation == 'download':
            self.operator = Download(self.file_path, self.socket, (self.host, self.port))
        else:
            raise ValueError("Invalid operation. Use 'upload' or 'download'.")

    def start(self) -> None:
        self.operator.start()
