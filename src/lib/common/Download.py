import os
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.packages.InitPackage import DownloadHeader
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
import logging
from lib.utils.logger import create_logger
from lib.utils.enums import PackageType, Protocol
from lib.protocols.stop_and_wait import StopAndWaitProtocol
from lib.protocols.selective_repeat import SelectiveRepeatProtocol


# class Download:
#     def __init__(
#         self,
#         file_path: str,
#         socket: Socket,
#         server_addr: ADDR,
#         protocol = Protocol.STOP_WAIT,
#         logging_level=logging.DEBUG,
#     ) -> None:
#         self.file_path = file_path
#         self.socket = socket
#         self.server_addr = server_addr
#         self.logger = create_logger(
#             "client-download", "[CLIENT DOWNLOAD]", logging_level
#         )
#         self.protocol = protocol

#     def start(self) -> None:
#         file_name = os.path.basename(self.file_path)
#         print("filepath", self.file_path)

#         # 1. Enviar paquete INIT de descarga
#         header = DownloadHeader(file_name)
#         self.socket.sendto(header, self.server_addr)

#         # 2. Esperar ACK
#         self.socket.recv()

#         sequence_number = 0
#         with open(self.file_path, "wb") as file:
#             while True:
#                 data, server_addr = self.socket.recv()

#                 # 3. Ver si es FIN
#                 # Si el paquete es un FIN, se cierra la conexión
#                 fin_packatge_type = str(PackageType.FIN.value) + SEPARATOR
#                 if data.decode().startswith(fin_packatge_type):
#                     self.logger.info("Received FIN package.")
#                     self.send_ack()
#                     break

#                 # 4. Sino, es un DataPackage
#                 data_package = DataPackage.from_bytes(data)
#                 print("data: ", data_package.data)
#                 file.write(data_package.data)
#                 file.flush()

#                 # 5. ACK por cada paquete
#                 self.send_ack(sequence_number)
#                 sequence_number ^= 1 # TODO: Implement a better sequence number handling

#         self.logger.info(f"File {file_name} downloaded successfully.")

#         fin_package = FinPackage()
#         self.socket.sendto(fin_package, self.server_addr)
#         self.socket.close()

#     def send_ack(self, sequence_number: int = 0) -> None:
#         ack = AckPackage(sequence_number)
#         self.socket.sendto(ack, self.server_addr)


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

        if protocol == Protocol.STOP_WAIT:
            self.protocol_handler = StopAndWaitProtocol(socket, server_addr)
        elif protocol == Protocol.SELECTIVE_REPEAT:
            self.protocol_handler = SelectiveRepeatProtocol(socket, server_addr)
        else:
            raise ValueError("Unsupported protocol")

    def start(self) -> None:
        file_name = os.path.basename(self.file_path)
        self.logger.info(f"Starting download of file: {file_name}")

        # 1. Enviar paquete INIT de descarga
        header = DownloadHeader(file_name)
        self.socket.sendto(header, self.server_addr)
        self.logger.debug(
            f"Sent download INIT header for {file_name} to {self.server_addr}"
        )

        # 2. Esperar ACK del servidor al INIT
        ack_init, _ = self.socket.recv()
        ack_package = AckPackage.from_bytes(ack_init)
        self.logger.debug(
            f"Received ACK for INIT: SeqNum={ack_package.sequence_number}"
        )

        with open(self.file_path, "wb") as file:
            print("filepath", self.file_path)
            self.logger.info(f"Opening file {self.file_path} for writing.")
            while True:
                # Recibir el paquete del servidor usando el handler de protocolo
                received_data = self.protocol_handler.receive()

                if received_data is None:
                    self.logger.info("Connection closed by server or FIN received.")
                    break  # Fin de la transmisión

                package_type = int(received_data[:1].decode())

                if package_type == PackageType.DATA.value:
                    data_package = DataPackage.from_bytes(received_data)
                    self.logger.debug(
                        f"Received data chunk with sequence number: {data_package.sequence_number}, size: {len(data_package.data)}"
                    )
                    file.write(data_package.data)
                    file.flush()
                    # El ACK se envía internamente en el método receive del protocolo
                elif package_type == PackageType.FIN.value:
                    self.logger.info("Received FIN package from server.")
                    # Enviar ACK al FIN
                    fin_ack = AckPackage()
                    self.socket.sendto(fin_ack, self.server_addr)
                    self.logger.debug("Sent ACK for FIN.")
                    break
                else:
                    self.logger.warning(
                        f"Received unknown package type: {package_type}"
                    )
                    break

        self.logger.info(
            f"File {file_name} downloaded successfully to {self.file_path}"
        )
        self.socket.close()
