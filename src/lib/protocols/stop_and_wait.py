from lib.packages.AckPackage import AckPackage
from lib.utils.types import ADDR
from lib.utils.Socket import Socket
from lib.packages.DataPackage import DataPackage
from lib.utils.constants import SEPARATOR, BUFSIZE
from lib.server.client_info import ClientInfo
import os
import time
from lib.utils.constants import SERVER_STORAGE
from lib.utils.logger import create_logger
import logging

TIMEOUT_SECONDS = 2.0  # puedes ajustar este valor


class StopAndWaitProtocol:
    def __init__(self, socket: Socket, send_to_addr: ADDR, logging_level=logging.DEBUG):
        self.socket = socket
        self.send_to_addr = send_to_addr
        self.sequence_number = 0
        self.last_ack = -1

        self.logger = create_logger(
            "client-download", "[CLIENT DOWNLOAD]", logging_level
        )

    # ----------------------    CLIENTE    ---------------------- #
    def send(self, data: bytes) -> None:
        # Crea un paquete de datos con el número de secuencia
        data_package = DataPackage(data, self.sequence_number)

        # Envía el paquete al servidor
        self.socket.sendto(data_package, self.send_to_addr)

        # Espera la confirmación (ACK)
        ack, _ = self.socket.recv()

        # Procesa el ACK recibido
        ack_package = AckPackage.from_bytes(ack)

        # Si el número de secuencia no coincide, vuelve a enviar el paquete
        if ack_package.sequence_number != self.sequence_number:
            self.send(data)  # Retransmite si el número de secuencia no coincide
        else:
            self.sequence_number ^= 1

    # Dentro de la clase StopAndWaitProtocol en el cliente

    def receive(self) -> bytes | None:
        """
        Recibe un paquete de datos del servidor y envía el ACK correspondiente (Stop and Wait).
        """
        while True:
            try:
                data, _ = self.socket.recv()
                received_package_type = int(data[:1].decode())

                if received_package_type == 4:  # PackageType.FIN.value
                    self.logger.info("Received FIN, sending ACK.")
                    ack = AckPackage()
                    self.socket.sendto(ack, self.send_to_addr)
                    return data
                elif received_package_type == 2:  # PackageType.DATA.value
                    data_package = DataPackage.from_bytes(data)

                    if data_package.sequence_number == self.sequence_number:
                        self.logger.debug(
                            f"Received data packet with expected sequence number: {data_package.sequence_number}"
                        )
                        # Enviar ACK con el número de secuencia recibido
                        ack = AckPackage(data_package.sequence_number)
                        self.socket.sendto(ack, self.send_to_addr)
                        self.sequence_number ^= (
                            1  # Alternar el número de secuencia esperado
                        )
                        return data
                    else:
                        self.logger.warning(
                            f"Received unexpected sequence number. Expected: {self.sequence_number}, Got: {data_package.sequence_number}. Sending ACK for the expected sequence number."
                        )
                        # Reenviar ACK del último paquete recibido correctamente (el esperado)
                        ack = AckPackage(self.sequence_number ^ 1)
                        self.socket.sendto(ack, self.send_to_addr)
                        # Descartar el paquete inesperado y esperar el correcto
                else:
                    self.logger.warning(
                        f"Received unknown package type: {received_package_type}"
                    )
                    return None

            except TimeoutError:
                self.logger.warning("Timeout while waiting for data.")
                return None
            except Exception as e:
                self.logger.error(f"Error during receive: {e}")
                return None

    # ----------------------    SERVIDOR    ---------------------- #

    # def handle_data(self, data: bytes, client_info: ClientInfo):
    #     _, seq_number, package_data = data.split(SEPARATOR.encode("utf-8"))

    #     if client_info.file is None:
    #         client_info.file = open(f"{client_info.filename}", "ab+")

    #     client_info.file.write(package_data)

    #     ack = AckPackage(int(seq_number))
    #     self.socket.sendto(ack, self.send_to_addr)

    def handle_data(self, data: bytes, client_info: ClientInfo):
        # Separar el paquete
        parts = data.split(SEPARATOR.encode("utf-8"), 2)

        # Verificar que el paquete esté correctamente formado
        if len(parts) < 3:
            print("[ERROR] Paquete malformado")
            return

        _, seq_number, package_data = parts

        # Si el archivo aún no ha sido abierto, lo abrimos en modo append
        if client_info.file is None:
            filepath = os.path.join(SERVER_STORAGE, client_info.filename)
            client_info.file = open(filepath, "ab+")

        # Escribir los datos en el archivo
        print(
            f"[INFO] Escribiendo datos en el archivo {client_info.filename}. Datos: {package_data}"
        )
        client_info.file.write(package_data)

        # Hacer flush para asegurar que se escriban en el disco
        client_info.file.flush()

        # Enviar el ACK al cliente
        ack = AckPackage(int(seq_number))
        self.socket.sendto(ack, self.send_to_addr)

        # Si hemos recibido el paquete de terminación (4|), cerramos el archivo
        if seq_number == "4":  # Suponiendo que 4 es el código de terminación
            if client_info.file:
                print(
                    f"[INFO] Finalizando la escritura en el archivo {client_info.filename}"
                )
                client_info.file.flush()  # Asegurarnos de que todo se haya escrito
                client_info.file.close()
                client_info.file = None  # Liberar el archivo

    def handle_download(self, client_info: ClientInfo):
        sequence_number = 0
        fd = client_info.file_descriptor

        while True:
            chunk = os.read(fd, BUFSIZE - 50)
            if not chunk:
                break

            package = DataPackage(chunk, sequence_number)
            self.socket.sendto(package, self.send_to_addr)

            start_time = time.time()

            while self.last_ack != sequence_number:
                if time.time() - start_time > TIMEOUT_SECONDS:
                    print(
                        f"[TIMEOUT] No ACK for seq={sequence_number}, retransmitiendo..."
                    )
                    self.socket.sendto(package, self.send_to_addr)
                    start_time = time.time()

                time.sleep(0.01)

            # ACK correcto recibido, cambiamos número de secuencia
            sequence_number ^= 1

    def handle_ack(self, data: bytes, client_info: ClientInfo):
        ack = AckPackage.from_bytes(data)
        self.last_ack = ack.sequence_number
