import logging
import os
from lib.utils.types import REQUEST
from lib.utils.constants import SEPARATOR
from lib.packages.InitPackage import InitPackage
from lib.utils.enums import PackageType
from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.utils.constants import Protocol
from lib.protocols.stop_and_wait import StopAndWaitProtocol
from lib.protocols.selective_repeat import SelectiveRepeatProtocol
from lib.server.client_info import ClientInfo
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
from lib.packages.FinPackage import FinPackage
from lib.utils.constants import BUFSIZE
from lib.utils.types import ADDR
import threading

PROTOCOL = Protocol.STOP_WAIT


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
            try:
                package = InitPackage.from_bytes(data)
                operation = package.operation
                file_path = f"{self.server_storage}/{package.get_file_name_without_extension()}.{package.get_file_extension()}"

                if operation == "upload":
                    file_descriptor = os.open(
                        file_path,
                        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                    )
                elif operation == "download":
                    file_descriptor = os.open(
                        file_path,
                        os.O_RDONLY,
                    )
                else:
                    self.logger.error(
                        f"Unknown operation requested by {addr_str}: {operation}"
                    )
                    return

                self.protocol = PROTOCOL

                if self.protocol == Protocol.STOP_WAIT:
                    handler = StopAndWaitProtocol(self.socket, addr)
                elif self.protocol == Protocol.SELECTIVE_REPEAT:
                    handler = SelectiveRepeatProtocol(self.socket, addr)
                else:
                    raise ValueError("Unknown protocol")

                client_info = ClientInfo(
                    addr=addr,
                    operation=operation,
                    file_descriptor=file_descriptor,
                    last_package_type=PackageType.INIT,
                    filename=package.file_name,
                    protocol_handler=handler,
                )
                self.clients[addr_str] = client_info
                self.logger.info(
                    f"New client connected: {addr_str} with operation {operation} for file {package.file_name}"
                )
                self.send_init_response(client_info)  # Send ACK after processing INIT

                if operation == "download":
                    # Ejecutar la descarga en un hilo separado
                    download_thread = threading.Thread(
                        target=self._handle_download_threaded, args=(client_info,)
                    )
                    download_thread.start()

            except Exception as e:
                self.logger.error(
                    f"Error processing initial package from {addr_str}: {e}"
                )
                return

        else:
            client_info = self.clients[addr_str]
            package_info = data.split(SEPARATOR.encode("utf-8"))
            package_type = int(package_info[0].decode("utf-8"))
            client_info.last_package_type = PackageType(package_type)

            if client_info.last_package_type == PackageType.DATA:
                client_info.protocol_handler.handle_data(data, client_info)
            elif client_info.last_package_type == PackageType.ACK:
                if client_info.operation == "download":
                    client_info.protocol_handler.handle_ack(data, client_info)
                else:
                    print("[REQUEST HANDLER] Unexpected ACK during upload (ignored)")
            elif client_info.last_package_type == PackageType.FIN:
                self.handle_finish_request(client_info)
            else:
                self.logger.error(
                    f"Unknown package type for client {addr_str}: {client_info.last_package_type}"
                )

    def _handle_download_threaded(self, client_info: ClientInfo):
        """Maneja la lógica de descarga en un hilo separado."""
        client_info.protocol_handler.handle_download(client_info)

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
