import os
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.packages.InitPackage import DownloadHeader
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
import logging
from lib.utils.logger import create_logger


class Download:
    def __init__(
        self,
        file_path: str,
        socket: Socket,
        server_addr: ADDR,
        logging_level=logging.DEBUG,
    ) -> None:
        self.file_path = file_path
        self.socket = socket
        self.server_addr = server_addr
        self.logger = create_logger(
            "client-download", "[CLIENT DOWNLOAD]", logging_level
        )

    def start(self) -> None:
        file_name = os.path.basename(self.file_path)
        print("filepath", self.file_path)

        # 1. Enviar paquete INIT de descarga
        header = DownloadHeader(file_name)
        self.socket.sendto(header, self.server_addr)

        # 2. Esperar ACK
        self.socket.recv()

        with open(self.file_path, "wb") as file:
            while True:
                data, server_addr = self.socket.recv()

                # 3. Ver si es FIN
                if data.startswith(b"FIN|"):
                    self.logger.info("Received FIN package.")
                    self.send_ack()
                    break

                # 4. Sino, es un DataPackage
                data_package = DataPackage.from_bytes(data)
                print("data: ", data_package.data)
                file.write(data_package.data)
                file.flush()

                # 5. ACK por cada paquete
                self.send_ack()

        self.logger.info(f"File {file_name} downloaded successfully.")
        self.socket.close()

    def send_ack(self):
        ack = AckPackage()
        self.socket.sendto(ack, self.server_addr)
