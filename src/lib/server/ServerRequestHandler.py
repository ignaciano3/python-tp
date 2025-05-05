from dataclasses import dataclass
import logging
import os
from lib.utils.types import REQUEST
from lib.utils.constants import OPERATION, SEPARATOR
from lib.utils.types import ADDR
from lib.packages.InitPackage import InitPackage
from lib.utils.enums import PackageType
from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.packages.AckPackage import AckPackage


@dataclass
class ClientInfo:
    addr: ADDR
    operation: OPERATION
    file_descriptor: int
    last_package_type: PackageType
    filename: str


class ServerRequestHandler:
    """
    Handles server requests and responses.
    """

    def __init__(self, server_storage: str, socket: Socket, logging_level = logging.DEBUG) -> None:
        self.clients: dict[str, ClientInfo] = {}
        self.server_storage = server_storage
        self.socket = socket
        self.logger = create_logger("request-handler", "[REQUEST HANDLER]", logging_level)

    def handle_request(self, request: REQUEST):
        self.logger.info(f"Handling request: {request}")
        data, addr = request

        addr_str = f"{addr[0]}:{addr[1]}"
        if addr_str not in self.clients:
            package = InitPackage.from_bytes(data)
            file_path = f"{self.server_storage}/{package.get_file_name_without_extension()}.{package.get_file_extension()}"
            file_descriptor = os.open(
                file_path,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            )
            self.clients[addr_str] = ClientInfo(
                addr=addr,
                operation=package.operation,
                file_descriptor=file_descriptor,
                last_package_type=PackageType.INIT,
                filename=package.file_name,
            )
            self.logger.info(
                f"New client connected: {addr_str} with operation {package.operation}"
            )

        client_info = self.clients[addr_str]

        package_info = data.split(SEPARATOR.encode("utf-8"))
        package_type = int(package_info[0].decode("utf-8"))
        client_info.last_package_type = PackageType(package_type)

        if client_info.last_package_type == PackageType.INIT:
            self.send_init_response(client_info)
        elif client_info.last_package_type == PackageType.DATA:
            self.handle_data_request(data, client_info)
        elif client_info.last_package_type == PackageType.FIN:
            self.handle_finish_request(client_info)
        else:
            self.logger.error(
                f"Unknown package type for client {addr_str}: {client_info.last_package_type}"
            )

    def handle_upload_request(self, data: bytes, client_info: ClientInfo):
        with open(f"{self.server_storage}/{client_info.filename}", "ab+") as file:
            file.write(data.split(SEPARATOR.encode("utf-8"))[1])
            file.flush()

        self.logger.info(f"File uploaded successfully from {client_info.addr}")

        self.send_ack(client_info.addr)

    def handle_download_request(self, data: bytes, client_info: ClientInfo):
        pass

    def send_init_response(self, client_info: ClientInfo):
        self.send_ack(client_info.addr)

    def handle_data_request(self, data: bytes, client_info: ClientInfo):
        if client_info.operation == "upload":
            self.handle_upload_request(data, client_info)
        elif client_info.operation == "download":
            self.handle_download_request(data, client_info)
        else:
            self.logger.error(
                f"Unknown operation for client {client_info.addr}: {client_info.operation}"
            )

    def handle_finish_request(self, client_info: ClientInfo):
        self.logger.info(f"File transfer finished from {client_info.addr}")
        self.send_ack(client_info.addr)
        os.close(client_info.file_descriptor)
        del self.clients[f"{client_info.addr[0]}:{client_info.addr[1]}"]

    def send_ack(self, addr: ADDR):
        ack_package = AckPackage()
        self.socket.sendto(ack_package, addr)
        self.logger.info(f"ACK sent to {addr}")
