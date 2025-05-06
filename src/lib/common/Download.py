import os
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.packages.InitPackage import DownloadHeader
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
import logging
from lib.utils.logger import create_logger
from lib.utils.enums import PackageType, Protocol
from lib.utils.constants import SEPARATOR
from lib.packages.FinPackage import FinPackage


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

    def start(self) -> None:
        file_name = os.path.basename(self.file_path)
        print("filepath", self.file_path)

        # 1. Enviar paquete INIT de descarga
        header = DownloadHeader(file_name)
        self.socket.sendto(header, self.server_addr)

        # 2. Esperar ACK
        self.socket.recv()
        fin_packatge_type = str(PackageType.FIN.value) + SEPARATOR
        sequence_number = 0
        self.send_ack(sequence_number)

        ## Protocolo ///

        with open(self.file_path, "wb") as file:
            while True:
                data, server_addr = self.socket.recv()

                # 3. Ver si es FIN
                # Si el paquete es un FIN, se cierra la conexión

                if data.decode().startswith(fin_packatge_type):
                    file.flush()
                    self.logger.info("Received FIN package.")
                    break

                # 4. Sino, es un DataPackage
                data_package = DataPackage.from_bytes(data)
                print("data: ", data_package.data)
                file.write(data_package.data)
                # file.flush()

                # 5. ACK por cada paquete
                self.send_ack(sequence_number)
                sequence_number ^= (
                    1  # TODO: Implement a better sequence number handling
                )
        ## Protocolo ///

        self.logger.info(f"File {file_name} downloaded successfully.")

        fin_package = FinPackage()
        self.socket.sendto(fin_package, self.server_addr)

        self.socket.recv()

        self.socket.close()

    def send_ack(self, sequence_number: int = 0) -> None:
        ack = AckPackage(sequence_number)
        self.socket.sendto(ack, self.server_addr)
