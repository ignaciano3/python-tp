import logging
import os
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.packages.InitPackage import UploadHeader
from lib.utils.logger import create_logger
from lib.packages.FinPackage import FinPackage
from lib.protocols.stop_and_wait import StopAndWaitProtocol
from lib.protocols.selective_repeat import SelectiveRepeatProtocol
from lib.utils.enums import Protocol


class Upload:
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
        self.protocol = protocol
        self.logger = create_logger("client", "[CLIENT]", logging_level)
        self.sequence_number = 0

        if protocol.value == Protocol.STOP_WAIT.value:
            self.protocol_handler = StopAndWaitProtocol(socket, server_addr)
        elif protocol.value == Protocol.SELECTIVE_REPEAT.value:
            self.protocol_handler = SelectiveRepeatProtocol(socket, server_addr)
        else:
            raise ValueError("Unsupported protocol")

    def start(self) -> None:
        if not os.path.isfile(self.file_path):
            self.logger.error(f"No se encontró el archivo: {self.file_path}")
            return

        file_name = os.path.basename(self.file_path)

        # Enviar el header de la carga de archivo
        header = UploadHeader(file_name)
        self.socket.sendto(header, self.server_addr)
        self.socket.recv()  # Esperar respuesta de servidor

        ## Protocolo ///

        with open(self.file_path, "rb") as file:
            self.protocol_handler.send(file)

        fin_package = FinPackage()
        self.socket.sendto(fin_package, self.server_addr)

        self.socket.recv()  # Esperar confirmación del servidor
        self.socket.close()

        self.logger.info(f"File {file_name} uploaded successfully.")
