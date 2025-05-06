import os
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.packages.InitPackage import DownloadHeader
from lib.packages.AckPackage import AckPackage
import logging
from lib.utils.logger import create_logger
from lib.utils.enums import PackageType, Protocol
from lib.packages.FinPackage import FinPackage
from lib.protocols.selective_repeat import SelectiveRepeatProtocol
from lib.protocols.stop_and_wait import StopAndWaitProtocol
from lib.packages.DataPackage import DataPackage
from lib.utils.constants import SEPARATOR


class Download:
    def __init__(
        self,
        file_path: str,
        socket: Socket,
        server_addr: ADDR,
        protocol=Protocol.STOP_WAIT,
        logging_level=logging.DEBUG,
    ) -> None:
        self.file_path = file_path
        self.socket = socket
        self.server_addr = server_addr
        self.logger = create_logger(
            "client-download", "[CLIENT DOWNLOAD]", logging_level
        )
        self.protocol = protocol

        if protocol.value == Protocol.STOP_WAIT.value:
            self.protocol_handler = StopAndWaitProtocol(socket, server_addr)
        elif protocol.value == Protocol.SELECTIVE_REPEAT.value:
            self.protocol_handler = SelectiveRepeatProtocol(socket, server_addr)
        else:
            raise ValueError("Unsupported protocol")

    def start(self) -> None:
        file_name = os.path.basename(self.file_path)
        print("filepath", self.file_path)

        # 1. Enviar paquete INIT de descarga
        header = DownloadHeader(file_name)
        self.socket.sendto(header, self.server_addr)

        # 2. Esperar ACK
        self.socket.recv()

        self.send_ack(0)

        finished = False
        with open(self.file_path, "wb") as file:
            while not finished:
                package, _ = self.socket.recv()

                finished = self.protocol_handler.receive(package, file)

        self.logger.info(f"File {file_name} downloaded successfully.")

        fin_package = FinPackage()
        self.socket.sendto(fin_package, self.server_addr)

        self.socket.recv()

        self.socket.close()

    def send_ack(self, sequence_number: int = 0) -> None:
        ack = AckPackage(sequence_number)
        self.socket.sendto(ack, self.server_addr)
