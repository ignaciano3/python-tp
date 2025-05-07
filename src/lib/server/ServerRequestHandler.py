from dataclasses import dataclass
from io import BufferedRandom
import logging
from lib.utils.types import REQUEST
from lib.utils.constants import OPERATION, BUFSIZE
from lib.utils.types import ADDR
from lib.packages.InitPackage import InitPackage
from lib.utils.enums import PackageType
from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.packages.AckPackage import AckPackage
from lib.packages.DataPackage import DataPackage
from lib.packages.FinPackage import FinPackage


@dataclass
class ClientInfo:
    addr: ADDR
    operation: OPERATION
    last_package_type: PackageType
    filename: str
    file: BufferedRandom | None = None
    seq_number: int = 0


class ServerRequestHandler:
    """
    Handles server requests and responses.
    """

    def __init__(
        self, server_storage: str, socket: Socket, logging_level=logging.DEBUG
    ) -> None:
        self.clients: dict[str, ClientInfo] = {}
        self.server_storage = server_storage
        self.socket = socket
        self.logger = create_logger(
            "request-handler", "[REQUEST HANDLER]", logging_level
        )

    def handle_request(self, request: REQUEST):
        self.logger.info(f"Handling request: {request}")
        package, addr = request

        addr_str = f"{addr[0]}:{addr[1]}"
        if addr_str not in self.clients:
            if not isinstance(package, InitPackage):
                self.logger.error(
                    f"Received unexpected package from {addr_str}: {package}"
                )
                return

            self.clients[addr_str] = ClientInfo(
                addr=addr,
                operation=package.operation,
                last_package_type=PackageType.INIT,
                filename=package.file_name,
            )
            self.logger.info(
                f"New client connected: {addr_str} with operation {package.operation}"
            )

        client_info = self.clients[addr_str]

        if isinstance(package, InitPackage):
            self.send_init_response(client_info)
        elif isinstance(package, DataPackage):
            self.handle_upload_request(package, client_info)
        elif isinstance(package, AckPackage):
            if client_info.operation == "download":
                self.handle_download_request(package, client_info)
            else:
                self.logger.info(
                    "[REQUEST HANDLER] Unexpected ACK during upload (ignored)"
                )
        elif isinstance(package, FinPackage):
            self.handle_finish_request(client_info)
        else:
            self.logger.error(
                f"Unknown package type for client {addr_str}: {client_info.last_package_type}"
            )

    def handle_upload_request(self, package: DataPackage, client_info: ClientInfo):
        if client_info.file is None:
            file = open(f"{self.server_storage}/{client_info.filename}", "ab+")
            client_info.file = file
        else:
            file = client_info.file

        file.write(package.data)

        self.logger.info(f"File written successfully from {client_info.addr}")

        self.send_ack(client_info.addr, int(package.sequence_number))

    def handle_download_request(self, package: AckPackage, client_info: ClientInfo):
        if client_info.file is None:
            file = open(f"{self.server_storage}/{client_info.filename}", "rb+")
            client_info.file = file
        else:
            file = client_info.file

        chunk = file.read(BUFSIZE - 50)

        if not chunk:
            self.logger.info(f"File transfer finished for {client_info.addr}")
            self.send_fin(client_info.addr)
            return

        data_package = DataPackage(chunk, client_info.seq_number)
        self.socket.sendto(data_package, client_info.addr)

    def send_init_response(self, client_info: ClientInfo):
        self.send_ack(client_info.addr)

    def handle_finish_request(self, client_info: ClientInfo):
        self.logger.warning(f"File transfer finished from {client_info.addr}")
        self.send_ack(client_info.addr)

        if client_info.file:
            client_info.file.close()
            client_info.file = None

        del self.clients[f"{client_info.addr[0]}:{client_info.addr[1]}"]

    def send_ack(self, addr: ADDR, seq_num: int = 0):
        ack_package = AckPackage(seq_num)
        self.socket.sendto(ack_package, addr)
        self.logger.info(f"ACK sent to {addr} with seq_num {seq_num}")

    def send_fin(self, addr: ADDR):
        fin_package = FinPackage()
        self.socket.sendto(fin_package, addr)
        self.logger.info(f"FIN sent to {addr}")
