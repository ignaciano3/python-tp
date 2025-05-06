import logging
import os
from lib.utils.types import REQUEST
from lib.utils.constants import SEPARATOR, BUFSIZE
from lib.utils.types import ADDR
from lib.packages.InitPackage import InitPackage
from lib.utils.enums import PackageType
from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.packages.AckPackage import AckPackage
from lib.packages.DataPackage import DataPackage
from lib.packages.FinPackage import FinPackage
from lib.utils.constants import Protocol
from lib.protocols.stop_and_wait import StopAndWaitProtocol
from lib.protocols.selective_repeat import SelectiveRepeatProtocol
from lib.server.client_info import ClientInfo

PROTOCOL = Protocol.STOP_WAIT


# @dataclass
# class ClientInfo:
#     addr: ADDR
#     operation: OPERATION
#     file_descriptor: int
#     last_package_type: PackageType
#     filename: str
#     file: BufferedRandom | None = None
#     protocol_handler: object | None = None


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
        data, addr = request

        addr_str = f"{addr[0]}:{addr[1]}"
        if addr_str not in self.clients:
            package = InitPackage.from_bytes(data)
            file_path = f"{self.server_storage}/{package.get_file_name_without_extension()}.{package.get_file_extension()}"
            if package.operation == "upload":
                file_descriptor = os.open(
                    file_path,
                    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                )
            else:
                # Open existing file for reading
                file_descriptor = os.open(
                    file_path,
                    os.O_RDONLY,
                )
            self.protocol = PROTOCOL  ##########################################cambiar

            if self.protocol == Protocol.STOP_WAIT:
                handler = StopAndWaitProtocol(self.socket, addr)
            elif self.protocol == Protocol.SELECTIVE_REPEAT:
                handler = SelectiveRepeatProtocol(self.socket, addr)
            else:
                raise ValueError("Unknown protocol")

            self.clients[addr_str] = ClientInfo(
                addr=addr,
                operation=package.operation,
                file_descriptor=file_descriptor,
                last_package_type=PackageType.INIT,
                filename=package.file_name,
                protocol_handler=handler,
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
            if client_info.operation == "download":
                # self.handle_download_request(data, client_info)
                client_info.protocol_handler.handle_download(client_info)

        elif client_info.last_package_type == PackageType.DATA:
            client_info.protocol_handler.handle_data(data, client_info)
            # self.handle_data_request(data, client_info)

        elif client_info.last_package_type == PackageType.ACK:
            if client_info.operation == "download":
                client_info.protocol_handler.handle_ack(data, client_info)
                # print("[REQUEST HANDLER] ACK received during download (ignored)")
            else:
                print("[REQUEST HANDLER] Unexpected ACK during upload (ignored)")
        elif client_info.last_package_type == PackageType.FIN:
            self.handle_finish_request(client_info)
        else:
            self.logger.error(
                f"Unknown package type for client {addr_str}: {client_info.last_package_type}"
            )

    def handle_upload_request(self, data: bytes, client_info: ClientInfo):
        _, seq_number, package_data = data.split(SEPARATOR.encode("utf-8"))

        if client_info.file is None:
            file = open(f"{self.server_storage}/{client_info.filename}", "ab+")
            client_info.file = file
        else:
            file = client_info.file

        file.write(package_data)

        self.logger.info(f"File written successfully from {client_info.addr}")

        self.send_ack(client_info.addr, int(seq_number))

    def handle_download_request(self, data: bytes, client_info: ClientInfo):
        file_descriptor = client_info.file_descriptor

        if file_descriptor is None:
            self.logger.error("No file descriptor available for download.")
            return

        sequence_number = 0

        try:
            while True:
                chunk = os.read(file_descriptor, BUFSIZE - 50)
                if not chunk:
                    break  # End of file

                data_package = DataPackage(chunk, sequence_number)
                self.socket.sendto(data_package, client_info.addr)
                self.logger.debug(f"Sent chunk to {client_info.addr}")

                # Wait for ACK
                self.socket.recv()
                sequence_number ^= (
                    1  # TODO: Implement a better sequence number handling
                )

            fin_package = FinPackage()
            self.socket.sendto(fin_package, client_info.addr)
            self.logger.info(f"File sent successfully to {client_info.addr}")

        except Exception as e:
            self.logger.error(f"Error while handling download request: {e}")

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
        self.logger.warning(f"File transfer finished from {client_info.addr}")
        self.send_ack(client_info.addr)
        os.close(client_info.file_descriptor)

        if client_info.file:
            client_info.file.close()
            client_info.file = None

        del self.clients[f"{client_info.addr[0]}:{client_info.addr[1]}"]

    def send_ack(self, addr: ADDR, seq_num: int = 0):
        ack_package = AckPackage(seq_num)
        self.socket.sendto(ack_package, addr)
        self.logger.info(f"ACK sent to {addr}")
