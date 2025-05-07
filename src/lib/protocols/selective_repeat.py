from dataclasses import dataclass
from io import BufferedReader, BufferedWriter
import logging
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.utils.constants import BUFSIZE
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
from lib.utils.logger import create_logger


@dataclass
class WindowItem:
    sequence_number: int
    data: bytes
    acked: bool = False


class Window:
    def __init__(self, size: int = 5):
        self.size = size  # Número de secuencia del primer paquete en la ventana
        self.items: list[WindowItem] = []  # ACKs recibidos en la ventana

    def length(self) -> int:
        return len(self.items)


class SelectiveRepeatProtocol:
    def __init__(self, socket: Socket, server_addr: ADDR, window_size: int = 5):
        self.socket = socket
        self.server_addr = server_addr
        self.window = Window(window_size)
        self.logger = create_logger(
            "selective_repeat", "[SELECTIVE REPEAT]", logging.DEBUG
        )
        self.last_sequence_number = 0
        self.first_sequence_number = 0

    def send(self, file: BufferedReader) -> None:
        finished = False
        while not finished:
            while self.window.length() < self.window.size:
                data = file.read(BUFSIZE - 16)

                if not data:
                    break

                data_package = DataPackage(data, self.last_sequence_number)
                self._send_package(data_package)

            if self.window.length() == 0:
                finished = True
                break
            self._receive_ack()

    def _send_package(self, package: DataPackage) -> None:
        self.socket.sendto(package, self.server_addr)
        self.logger.debug(
            f"Enviando paquete: {package.sequence_number}  - ({self.first_sequence_number} {self.last_sequence_number})"
        )
        self.window.items.append(WindowItem(package.sequence_number, package.data))
        self.last_sequence_number += 1

    def _receive_ack(self) -> None:
        # Espera la confirmación (ACK)
        self.socket.settimeout(1)  # Timeout de 1 segundo
        ack, _ = self.socket.recv()

        if not isinstance(ack, AckPackage):
            return

        self.logger.debug(
            f"Recibiendo ACK: {ack.sequence_number}  - ({self.first_sequence_number} {self.last_sequence_number})"
        )

        for item in self.window.items:
            if item.sequence_number == ack.sequence_number:
                item.acked = True
                break

        if ack.sequence_number != self.first_sequence_number:
            self.logger.debug(
                f"ACK no coincide: {ack.sequence_number} != {self.first_sequence_number}"
            )
        else:
            first_package = self.window.items[0]
            if first_package.sequence_number != ack.sequence_number:
                raise ValueError("El primer paquete no coincide con el ACK recibido")
            self.window.items.remove(first_package)
            self.first_sequence_number += 1

            if self.window.length() > 0:
                self._actualizar_window()

    def _actualizar_window(self) -> None:
        first_package = self.window.items[0]

        if first_package.acked:
            # caso en que llego en desorden algun paquete
            self.window.items.remove(first_package)
            self.logger.warning(
                f"Remuevo el paquete rezagado con seq_number {first_package.sequence_number} con ack true en la ventana"
            )
            self.first_sequence_number += 1
            self._actualizar_window()

    def receive(self, file: BufferedWriter) -> None:
        pass
