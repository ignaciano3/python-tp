from dataclasses import dataclass
from io import BufferedReader, BufferedWriter
import logging
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.utils.constants import BUFSIZE
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
from lib.utils.logger import create_logger
from lib.packages.Package import Package
from lib.utils.enums import PackageType


@dataclass
class WindowItem:
    sequence_number: int
    data: bytes
    acked: bool = False


class Window:
    def __init__(self, size: int = 5):
        self.size = size  # Número de secuencia del primer paquete en la ventana
        self.items: list[WindowItem] = []  # ACKs recibidos en la ventana

        self.last_sent_chunks = {}

    def length(self) -> int:
        return len(self.items)


class SelectiveRepeatProtocol:
    def __init__(
        self,
        socket: Socket,
        server_addr: ADDR,
        window_size: int = 5,
        from_stop_and_wait: bool = False,
    ) -> None:
        self.from_stop_and_wait = from_stop_and_wait
        self.socket = socket
        self.server_addr = server_addr
        self.window = Window(window_size)
        self.logger = create_logger(
            "selective_repeat", "[SELECTED REPEAT]", logging.DEBUG
        )
        self.last_sequence_number = 0
        self.first_sequence_number = 0
        self.tries = 0
        self.max_tries = 5

    # ---------------------------- SEND ---------------------------- #

    def send(self, file: BufferedReader) -> None:
        finished = False
        while not finished:
            while self.window.length() < self.window.size:
                data = file.read(BUFSIZE - 16)

                if not data:
                    break

                data_package = DataPackage(data, self.last_sequence_number)
                self._send_package(data_package)
                self.agregar_paquete_al_window(data_package)

            if self.window.length() == 0:
                finished = True
                break
            self._receive_ack()

    def _send_package(self, package: DataPackage) -> None:
        self.socket.sendto(package, self.server_addr)
        self.logger.debug(
            f"Enviando paquete: {package.sequence_number}  - ({self.first_sequence_number} {self.last_sequence_number})"
        )

    def obtener_proximo_seq_number(self, seq_number: int) -> int:
        if self.from_stop_and_wait:
            return seq_number ^ 1
        else:
            return seq_number + 1

    def agregar_paquete_al_window(self, package: DataPackage) -> None:
        self.window.items.append(WindowItem(package.sequence_number, package.data))
        self.last_sequence_number = self.obtener_proximo_seq_number(
            self.last_sequence_number
        )

    def _receive_ack(self) -> None:
        if self.tries >= self.max_tries:
            self.logger.error("Número máximo de reintentos alcanzado. Abortando.")
            raise Exception("Número máximo de reintentos alcanzado. Abortando.")

        # Espera la confirmación (ACK)
        self.socket.settimeout(10)  # Timeout de 1 segundo
        try:
            ack, _ = self.socket.recv()
        except TimeoutError:
            self.logger.debug("Timeout esperando ACK")

            # Es probable que el paquete se haya perdido, por lo tanto lo reenviamos
            data_package = DataPackage(
                self.window.items[0].data, self.first_sequence_number
            )
            self._send_package(data_package)
            self.tries += 1
            return
        except Exception as e:
            self.logger.error(f"Error inesperado al recibir el ACK: {e}")
            self.tries += 1
            raise

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
            if first_package.sequence_number < ack.sequence_number:
                self.logger.warning(
                    f"El servidor mando un paquete con seq_number {first_package.sequence_number} que no esta en la ventana"
                )
                # raise ValueError("El primer paquete no coincide con el ACK recibido")
                return

            self.window.items.remove(first_package)
            self.first_sequence_number = self.obtener_proximo_seq_number(
                self.first_sequence_number
            )

            if not self.from_stop_and_wait and self.window.length() > 0:
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

    # ---------------------------- RECEIVE ---------------------------- #

    def receive(self, file: BufferedWriter) -> None:
        finished = False

        while not finished:
            package, _ = self.socket.recv()
            finished = self._receive_aux(package, file)

    def _receive_aux(self, package: Package, file: BufferedWriter) -> bool:
        if package.type == PackageType.FIN or package.data is None:
            file.flush()
            return True

        if not package.valid:
            ack_package = AckPackage(self.sequence_number, False)
            self.socket.sendto(ack_package, self.server_addr)
            return False

        if package.type != PackageType.DATA:
            raise Exception("El paquete recibido no es un DataPackage.")

        file.write(package.data)

        ack_package = AckPackage(self.sequence_number)  # type: ignore
        self.socket.sendto(ack_package, self.server_addr)
        self.sequence_number += 1
        return False

    # ---------------------------- SERVER ---------------------------- #

    def get_window(self) -> Window:
        return self.window

    ################### USR LOS WINDOWS INFO
    def chunk_sent(self, chunk: bytes, seq_num: int) -> None:
        self.window.last_sent_chunks[seq_num] = chunk
        self.logger.debug(f"Chunk sent: {seq_num}")

    def get_chunk(self, seq_num: int) -> bytes:
        return self.window.last_sent_chunks.get(seq_num, b"")
