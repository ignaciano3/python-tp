import logging
from typing import Literal

from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.common.Upload import Upload
from lib.utils.constants import DEFAULT_PORT, DEFAULT_HOST, CLIENT_STORAGE
from lib.common.Download import Download


class Client:
    def __init__(
        self,
        operation: Literal["upload", "download"],
        file_name: str = "",
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        client_storage: str = CLIENT_STORAGE,
        logging_level=logging.DEBUG,
    ) -> None:
        self.host = host
        self.port = port
        self.operation = operation
        self.logger = create_logger("client", "[CLIENT]", logging_level)
        self.socket = Socket()
        self.file_name = file_name
        self.client_storage = client_storage

        if self.operation == 'upload':
            file_path = self.client_storage + "/" + self.file_name
            self.operator = Upload(file_path, self.socket, (self.host, self.port))
        elif self.operation == 'download':
            self.operator = Download(self.file_name, self.socket, (self.host, self.port))
        else:
            raise ValueError("Invalid operation. Use 'upload' or 'download'.")

    def start(self) -> None:
        self.operator.start()
